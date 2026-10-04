"""Reproducible internal experiment. Usage: python run_pipeline.py --input ../upload"""
from pathlib import Path
import argparse,json,hashlib,itertools,platform,sys
import numpy as np
import pandas as pd
from btf25 import *
from audit_dataset import audit_file,FILES
ROOT=Path(__file__).parent

def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x

def dump(path,x):path.write_text(json.dumps(clean(x),indent=2,ensure_ascii=False),encoding='utf8')

def verification(out):
    cfg=load_config();n=500;fs=cfg['fs_hz'];t=np.arange(n)/fs;rows=[]
    for f in [12.288,20.48,40.96,81.92,159.744,163.84,216.67,327.68,399.36]:
        errs=[]
        sos=np.vstack([butter(4,10,'high',fs=fs,output='sos'),butter(4,409.6,'low',fs=fs,output='sos')])
        _,h=sosfreqz(sos,worN=[2*np.pi*f/fs]);expected=abs(h[0])**2*1000/(2*np.pi*f*np.sqrt(2))
        for phase in np.arange(16)*2*np.pi/16:
            a=np.zeros((n,3));a[:,0]=np.sin(2*np.pi*f*t+phase)
            z=features(a,cfg);errs.append(abs(z['v_rms']/expected-1))
        rows.append({'frequency_hz':f,'max_relative_error':max(errs),'criterion': 'interior <1%' if f>=40 else 'boundary characterization','pass_required':bool(max(errs)<.01) if f>=40 else None})
    assert all(r['pass_required'] for r in rows if r['pass_required'] is not None)
    assert features(np.ones((500,3)))['v_rms']==0
    try:features(np.full((500,3),np.nan));raise AssertionError('NaN accepted')
    except ValueError:pass
    m=metrics([0,0,1,1],[0,1,1,1]);assert m['balanced_accuracy']==.75 and m['confusion']==[[1,1],[0,2]]
    fixture=np.c_[np.sin(2*np.pi*163.84*t),.7*np.cos(2*np.pi*40.96*t),.2*np.sin(2*np.pi*327.68*t)]
    np.savetxt(ROOT/'fixture_acceleration.csv',fixture,delimiter=',',header='X,Y,Z',comments='')
    z=features(fixture);dump(ROOT/'fixture_expected.json',{k:z[k].tolist() if isinstance(z[k],np.ndarray) else z[k] for k in ['r','energy','v_rms','delta_db']})
    pd.DataFrame(rows).to_csv(out/'synthetic_verification.csv',index=False)
    dump(out/'verification.json',{'synthetic_interior_pass':True,'parseval_checked_every_fragment':True,'zero_signal_pass':True,'nan_rejected':True,'manual_confusion_pass':True,'boundary_limitation':'12.288 Hz: about 3.83% phase-dependent error; no 1% full-band accuracy claim','matlab_executed':False})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--cache',type=Path);args=ap.parse_args()
    out=ROOT/'results';out.mkdir(exist_ok=True);verification(out);cfg=load_config();arrays={};manifest=[];records=[];raws=[];inventory=[]
    for filename,condition in FILES.items():
        path=args.input/filename;sha=hashlib.sha256(path.read_bytes()).hexdigest()
        cache=args.cache/(condition+'.npy') if args.cache else None
        if cache and cache.exists():
            # Cache only accepted against the original audit hash; default public run rebuilds from XLSX.
            audit=pd.read_csv(ROOT/'source_inventory.csv');assert sha==audit.loc[audit.condition==condition,'sha256'].iloc[0]
            arr=np.load(cache)
        else:
            audit_file(path,condition,cache=ROOT/'temporary_arrays');arr=np.load(ROOT/'temporary_arrays'/(condition+'.npy'))
        assert np.isfinite(arr).all() and np.all(np.diff(arr[:,0])>0)
        arrays[condition]=arr;inventory.append({'condition':condition,'filename':filename,'sha256':sha,'rows':len(arr)})
        t=arr[:,0];dt=np.diff(t);bounds=np.r_[0,np.flatnonzero(dt>cfg['gap_factor']*np.median(dt))+1,len(t)]
        for sid,(begin,end) in enumerate(zip(bounds[:-1],bounds[1:]),1):
            start=float(t[begin]-t[0]);stop=float(t[end-1]-t[0]);partition='excluded';block=0;reason='outside_intervals_or_crosses_boundary'
            if end-begin!=500:reason='not_500_samples'
            else:
                for part,key in [('development','development_intervals_s'),('test','test_intervals_s')]:
                    for j,(lo,hi) in enumerate(cfg[key],1):
                        if start>=lo and stop<hi:partition=part;block=j;reason='included'
            row={'condition':condition,'segment_id':sid,'begin_index':int(begin),'end_index_exclusive':int(end),'start_relative_s':start,'end_relative_s':stop,'n_samples':int(end-begin),'partition':partition,'block':block,'reason':reason};manifest.append(row)
            if partition!='excluded':
                a=arr[begin:end,1:];z=features(a,cfg)
                if z['degenerate']:row['partition']='excluded';row['reason']='zero_energy';continue
                feature={**row,'class_id':cfg['class_order'].index(condition),'v_rms':z['v_rms'],**{f'r{i}':float(z['r'][i]) for i in range(6)}}
                records.append(feature);raws.append(a)
    frame=pd.DataFrame(records);raw=np.asarray(raws);dev=frame[frame.partition=='development'];test=frame[frame.partition=='test']
    pd.DataFrame(manifest).to_csv(out/'fragment_manifest.csv',index=False);pd.DataFrame(inventory).to_csv(out/'input_hashes.csv',index=False)
    frame.to_csv(out/'features.csv',index=False)
    assert dev.end_relative_s.max()<250 and test.start_relative_s.min()>=252
    # Development cross-validation: all preprocessing fitted again; neighboring training fragments purged.
    cv=[]
    for held in range(1,5):
        val=dev[dev.block==held];lo,hi=cfg['development_intervals_s'][held-1]
        tr=dev[(dev.block!=held)&((dev.end_relative_s<lo-2)|(dev.start_relative_s>=hi+2))]
        pred=predict(val,fit_model(tr,cfg));pred['fold']=held;cv.append(pred)
    cv=pd.concat(cv);cv.to_csv(out/'development_cv_predictions.csv',index=False)
    cvmetrics={k:metrics((cv.class_id>0).astype(int),cv['pred_'+k]) for k in ['a','b']}
    # Freeze final parameters BEFORE evaluation on the held-out interval.
    model=fit_model(dev,cfg);dump(out/'frozen_parameters.json',model)
    provenance={'config':cfg,'input_hashes':inventory,'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'test_used_for_fitting':False}
    dump(out/'frozen_protocol.json',provenance)
    pred=predict(test,model);pred.to_csv(out/'test_predictions.csv',index=False);y=(pred.class_id>0).astype(int)
    results={k:metrics(y,pred['pred_'+k]) for k in ['a','b']};results['multiclass_a']=metrics(pred.class_id,pred.pred_multiclass,5)
    blocks=[]
    for (cls,b),g in pred.groupby(['class_id','block']):
        truth=(g.class_id>0).astype(int);ca=(g.pred_a==truth).sum();cb=(g.pred_b==truth).sum()
        blocks.append({'class_id':int(cls),'condition':cfg['class_order'][cls],'block':int(b),'n':len(g),'correct_a':int(ca),'correct_b':int(cb),'q_a':ca/len(g),'q_b':cb/len(g)})
    bf=pd.DataFrame(blocks);bf.to_csv(out/'block_indicators.csv',index=False)
    cluster=bf.groupby('class_id')[['n','correct_a','correct_b']].sum();d=(cluster.correct_a-cluster.correct_b)/cluster.n
    weights=np.r_[.5,.5*cluster.n.iloc[1:].to_numpy()/cluster.n.iloc[1:].sum()];obs=float(np.dot(weights,d));stats=[float(np.dot(weights,d*np.array(s))) for s in itertools.product([-1,1],repeat=5)]
    pvalue=sum(v>=obs-1e-14 for v in stats)/32
    boots=[]
    for choices in itertools.product(list(itertools.product([0,1],repeat=2)),repeat=5):
        aggregate=[]
        for cls,choice in enumerate(choices):aggregate.append(bf[bf.class_id==cls].iloc[list(choice)][['n','correct_a','correct_b']].sum().to_numpy())
        agg=np.array(aggregate);a=.5*(agg[0,1]/agg[0,0]+agg[1:,1].sum()/agg[1:,0].sum());b=.5*(agg[0,2]/agg[0,0]+agg[1:,2].sum()/agg[1:,0].sum());boots.append([a,b,a-b])
    ci=np.quantile(boots,[.025,.975],axis=0).tolist()
    results['exploratory_contrast']={'difference_ba_a_minus_b':obs,'one_sided_cluster_sign_p':pvalue,'patterns':32,'relevant_delta':.02,'decision':'internal evidence of relevant superiority' if pvalue<.05 and ci[0][2]>.02 else 'superiority not demonstrated','conditional_block_bootstrap_95_percent':{'a':[ci[0][0],ci[1][0]],'b':[ci[0][1],ci[1][1]],'difference':[ci[0][2],ci[1][2]]},'limitation':'Only five records, one per condition. Conditional sign exchangeability and within-record resampling; no inference to new sessions.'}
    noise=[];testidx=test.index.to_numpy()
    for snr in cfg['noise_snr_db']:
        for seed in cfg['noise_seeds']:
            rng=np.random.default_rng(seed);pert=test.copy();actual=[]
            for rowidx in testidx:
                a=raw[rowidx];center=a-a.mean(axis=0);power=np.mean(center**2,axis=0);eps=rng.normal(size=a.shape);eps-=eps.mean(axis=0);eps*=np.sqrt(power/(10**(snr/10)*np.mean(eps**2,axis=0)))
                z=features(a+eps,cfg);pert.loc[rowidx,[f'r{i}' for i in range(6)]]=z['r'];pert.loc[rowidx,'v_rms']=z['v_rms'];actual.extend((10*np.log10(power/np.mean(eps**2,axis=0))).tolist())
            pr=predict(pert,model);ma=metrics(y,pr.pred_a);mb=metrics(y,pr.pred_b)
            noise.append({'snr_db':snr,'seed':seed,'ba_a':ma['balanced_accuracy'],'ba_b':mb['balanced_accuracy'],'multiclass_accuracy':float(np.mean(pr.pred_multiclass==pr.class_id)),'realized_snr_min':min(actual),'realized_snr_max':max(actual)})
    pd.DataFrame(noise).to_csv(out/'noise_robustness.csv',index=False)
    results['development_cv']=cvmetrics;results['counts']=frame.groupby(['partition','condition','block']).size().reset_index(name='n').to_dict('records')
    dump(out/'results.json',results)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(8,3.4))
    for ax,key in zip(axs,['a','b']):
        cm=np.array(results[key]['confusion']);ax.imshow(cm,cmap='Blues');ax.set_title('BTF25' if key=='a' else 'Referencia RMS');ax.set_xticks([0,1],['Healthy','Fault']);ax.set_yticks([0,1],['Healthy','Fault']);ax.set_xlabel('Predicción');ax.set_ylabel('Real')
        for i,j in itertools.product(range(2),repeat=2):ax.text(j,i,str(cm[i,j]),ha='center',va='center')
    fig.tight_layout();fig.savefig(out/'binary_confusion.png',dpi=180);plt.close(fig)
    print(json.dumps(clean({k:results[k] for k in ['a','b','multiclass_a','exploratory_contrast']}),indent=2));print('DONE')
if __name__=='__main__':main()
