"""BTF25-v1: deterministic feature extraction and rule-based classification.
Spectral filtering is a new window-domain operator; it is NOT filtfilt on a record.
"""
from pathlib import Path
import json
import numpy as np
from scipy.signal import butter,sosfreqz,windows

def load_config():return json.loads((Path(__file__).parent/'config.json').read_text())

def features(acceleration,cfg=None,apply_filter=True):
    cfg=cfg or load_config();a=np.asarray(acceleration,dtype=float)
    if a.ndim!=2 or a.shape[1]!=3 or not np.isfinite(a).all():raise ValueError('Invalid triaxial input')
    n=len(a);fs=cfg['fs_hz'];f=np.fft.rfftfreq(n,1/fs)
    w=windows.hann(n,sym=False);u=np.mean(w*w)
    centered=a-a.mean(axis=0)
    A=np.fft.rfft(centered*w[:,None],axis=0)
    g=np.ones(len(f))
    if apply_filter:
        sos=np.vstack([butter(cfg['butterworth_order'],cfg['highpass_hz'],'high',fs=fs,output='sos'),
                       butter(cfg['butterworth_order'],cfg['lowpass_hz'],'low',fs=fs,output='sos')])
        _,h=sosfreqz(sos,worN=2*np.pi*f/fs);g=abs(h)**2
    mask=(f>=cfg['analysis_band_hz'][0])&(f<=cfg['analysis_band_hz'][1])
    mask[0]=False
    if n%2==0:mask[-1]=False
    V=np.zeros_like(A);V[mask]=1000*A[mask]*g[mask,None]/(1j*2*np.pi*f[mask,None])
    v=np.fft.irfft(V,n=n,axis=0)/np.sqrt(u)
    p=abs(V)**2/(fs*np.sum(w*w));p[1:-1 if n%2==0 else None]*=2
    axis_energy=p.sum(axis=0)*(fs/n)
    np.testing.assert_allclose(axis_energy,np.mean(v*v,axis=0),rtol=1e-11,atol=1e-12)
    total=float(np.sqrt(axis_energy.sum()))
    energy=[]
    for band in [cfg['reference_band_hz'],cfg['comparison_band_hz']]:
        bins=(f>=band[0])&(f<=band[1])
        if not np.any(bins):raise ValueError('Empty spectral band')
        energy.extend((p[bins].sum(axis=0)*(fs/n)).tolist())
    e=np.asarray(energy);floor=cfg['numeric_energy_floor']
    r=np.log10(np.maximum(e,floor))
    delta=10*np.log10((e[3:]+floor)/(e[:3]+floor))
    return {'r':r,'energy':e,'v_rms':total,'delta_db':delta,'frequency_hz':f,
            'velocity_power_spectrum':p,'weighted_velocity':v,
            'degenerate':axis_energy.sum()<=floor}

def robust_fit(x,floor=1e-12):
    m=np.median(x,axis=0);s=1.4826*np.median(abs(x-m),axis=0)
    q=np.quantile(x,[.25,.75],axis=0,method='linear');iqr=(q[1]-q[0])/1.349
    s=np.where(s>floor,s,iqr);active=s>floor
    if not active.any():raise ValueError('No nonconstant features')
    return {'median':m.tolist(),'scale':np.where(active,s,1).tolist(),'active':active.tolist()}

def normalized(x,model):
    active=np.asarray(model['active'],bool)
    return ((x-np.array(model['median']))/np.array(model['scale']))[:,active]

def fit_model(frame,cfg=None):
    cfg=cfg or load_config();cols=[f'r{i}' for i in range(6)]
    healthy=frame[frame.class_id==0]
    if not len(healthy):raise ValueError('Healthy development absent')
    norm=robust_fit(healthy[cols].to_numpy(),cfg['scale_floor'])
    score=np.max(abs(normalized(healthy[cols].to_numpy(),norm)),axis=1)
    multi=robust_fit(frame[cols].to_numpy(),cfg['scale_floor'])
    z=normalized(frame[cols].to_numpy(),multi);prototypes=[]
    for cls in range(1,5):
        grouped=[]
        for block in sorted(frame.loc[frame.class_id==cls,'block'].unique()):
            selected=(frame.class_id.to_numpy()==cls)&(frame.block.to_numpy()==block)
            grouped.append(np.median(z[selected],axis=0))
        if not grouped:raise ValueError(f'Class {cls} absent from development')
        prototypes.append(np.median(grouped,axis=0).tolist())
    vr=healthy.v_rms.to_numpy()
    return {'binary_normalization':norm,'threshold_a':float(np.quantile(score,cfg['healthy_percentile'],method='linear')),
            'p95_v':float(np.quantile(vr,cfg['healthy_percentile'],method='linear')),
            'p99_v':float(np.quantile(vr,cfg['alarm_percentile'],method='linear')),
            'multiclass_normalization':multi,'prototypes':prototypes,
            'class_order':cfg['class_order'],'fit_count':len(frame),'fit_healthy_count':len(healthy)}

def predict(frame,model):
    x=frame[[f'r{i}' for i in range(6)]].to_numpy()
    score=np.max(abs(normalized(x,model['binary_normalization'])),axis=1)
    a=(score>model['threshold_a']).astype(int)
    b=(frame.v_rms.to_numpy()>model['p95_v']).astype(int)
    u=normalized(x,model['multiclass_normalization'])
    distance=np.mean((u[:,None,:]-np.array(model['prototypes'])[None,:,:])**2,axis=2)
    multi=np.where(a==0,0,np.argmin(distance,axis=1)+1)
    v=frame.v_rms.to_numpy();level=np.where(v<=model['p95_v'],1,np.where(v<=model['p99_v'],2,3))
    out=frame.copy();out['score_a']=score;out['pred_a']=a;out['pred_b']=b
    out['pred_multiclass']=multi;out['velocity_level']=level
    out['prototype_tie']=np.sum(distance==distance.min(axis=1)[:,None],axis=1)>1
    return out

def confusion(y,p,nclasses):
    return np.bincount(np.asarray(y,int)*nclasses+np.asarray(p,int),minlength=nclasses**2).reshape(nclasses,nclasses)

def metrics(y,p,nclasses=2):
    cm=confusion(y,p,nclasses);total=cm.sum();tp=np.diag(cm).astype(float)
    actual=cm.sum(axis=1);predicted=cm.sum(axis=0)
    recall=np.divide(tp,actual,out=np.full(nclasses,np.nan),where=actual>0)
    precision=np.divide(tp,predicted,out=np.full(nclasses,np.nan),where=predicted>0)
    den=actual+predicted;f1=np.divide(2*tp,den,out=np.full(nclasses,np.nan),where=den>0)
    accuracy=float(tp.sum()/total);pe=float(np.dot(actual,predicted)/(total**2))
    result={'n':int(total),'confusion':cm.tolist(),'accuracy':accuracy,
            'balanced_accuracy':float(np.mean(recall)) if np.isfinite(recall).all() else None,
            'f1_macro':float(np.mean(f1)) if np.isfinite(f1).all() else None,
            'kappa':float((accuracy-pe)/(1-pe)) if pe<1 else None,
            'recall_by_class':recall.tolist(),'precision_by_class':precision.tolist(),'f1_by_class':f1.tolist()}
    if nclasses==2:
        tn,fp,fn,tp2=cm.ravel();result.update({'sensitivity':float(recall[1]),'specificity':float(recall[0]),
            'precision_fault':float(precision[1]) if predicted[1] else None,'fn':int(fn),'fp':int(fp),
            'fn_over_fp':float(fn/fp) if fp else ('infinity' if fn else None)})
    return result
