"""Auditoría reproducible de los XLSX originales BTF25; no ajusta clasificadores."""
from pathlib import Path
import argparse, csv, hashlib, json, platform, sys, time
import numpy as np
import openpyxl

FILES = {
    'Healthy.xlsx':'Healthy',
    'Damaged Bottom Right Blade.xlsx':'Damaged_LR',
    'Damaged Top Right Blade.xlsx':'Damaged_UR',
    'Unbalanced Bottom Right Blade.xlsx':'Unbalanced_LR',
    'Unbalanced Top Right Blade.xlsx':'Unbalanced_UR',
}

def write_csv(path, records):
    if not records: return
    with Path(path).open('w', newline='', encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]))
        writer.writeheader();writer.writerows(records)

def audit_file(path, condition, gap_factor=1.5, cache=None):
    started=time.perf_counter()
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    workbook=openpyxl.load_workbook(path,read_only=True,data_only=True)
    if len(workbook.worksheets)!=1:
        raise ValueError(f'{path.name}: se esperaba una hoja; revisar esquema.')
    sheet=workbook.worksheets[0]
    iterator=sheet.iter_rows(values_only=True); headers=list(next(iterator))
    data=[]; bad_rows=[]; string_cells=0; comments=[]; blank_tail_rows=0
    for excel_row, row in enumerate(iterator,2):
        if all(v is None for v in row):
            blank_tail_rows+=1;continue
        numeric=[]
        for column,v in enumerate(row[:4],1):
            string_cells+=isinstance(v,str)
            try:
                if v is None or isinstance(v,bool): raise ValueError()
                numeric.append(float(v))
            except (TypeError,ValueError):
                bad_rows.append({'condition':condition,'excel_row':excel_row,
                                 'column':column,'value':repr(v)})
                numeric.append(float('nan'))
        if len(numeric)!=4: raise ValueError(f'Fila incompleta {path.name}:{excel_row}')
        data.append(numeric)
        if len(row)>4 and any(v is not None for v in row[4:]):
            comments.append({'excel_row':excel_row,'extra_values':list(row[4:])})
    workbook.close()
    array=np.asarray(data,dtype=np.float64)
    if cache:
        Path(cache).mkdir(parents=True,exist_ok=True)
        np.save(Path(cache)/(condition+'.npy'),array)
    t=array[:,0]; acceleration=array[:,1:]
    if not np.isfinite(t).all(): raise ValueError(f'Tiempos no finitos: {path.name}')
    dt=np.diff(t)
    if np.any(dt<=0): raise ValueError(f'Tiempos no crecientes: {path.name}')
    nominal_dt=float(np.median(dt));cutoff=gap_factor*nominal_dt
    indices=np.flatnonzero(dt>cutoff)
    regular=dt[dt<=cutoff]
    boundaries=np.r_[0,indices+1,len(t)]
    segments=[]
    for segment_id,(begin,end) in enumerate(zip(boundaries[:-1],boundaries[1:]),1):
        t0=float(t[begin]);t1=float(t[end-1]);duration=t1-t0
        segments.append({'condition':condition,'segment_id':segment_id,
            'excel_start_row':int(begin)+2,'excel_end_row':int(end)+1,
            'n_samples':int(end-begin),'start_s':t0,'end_s':t1,
            'duration_s':duration})
    gaps=[{'condition':condition,'left_excel_row':int(i)+2,'right_excel_row':int(i)+3,
           'left_time_s':float(t[i]),'right_time_s':float(t[i+1]),
           'interval_s':float(dt[i]),'excess_over_nominal_s':float(dt[i]-nominal_dt)}
           for i in indices]
    durations=np.array([s['duration_s'] for s in segments])
    # Eligibility is conservative: observed span >= N/fs, no padding or edge trimming yet.
    window_counts={}
    for seconds in [0.125,0.25,0.5,1,2]:
        window_counts[str(seconds)]=int(np.floor(durations/seconds).sum())
    relative=t-t[0]
    dt_q=np.quantile(dt,[0,.01,.05,.5,.95,.99,1])
    reg_q=np.quantile(regular,[0,.01,.5,.99,1])
    stats={'filename':path.name,'condition':condition,'sheet':sheet.title,
        'bytes':path.stat().st_size,'sha256':digest,'rows_numeric':len(array),
        'columns':len(headers),'headers':headers,'string_cells_first_four':int(string_cells),
        'bad_conversion_cells':len(bad_rows),'nonfinite_cells':int((~np.isfinite(array)).sum()),
        'empty_rows_skipped':blank_tail_rows,'nonempty_extra_rows':len(comments),
        'extra_values_preview':comments[:10],'start_s':float(t[0]),'end_s':float(t[-1]),
        'duration_s':float(t[-1]-t[0]),'dt_median_s':nominal_dt,
        'fs_inverse_median_hz':1/nominal_dt,'fs_regular_mean_hz':1/float(regular.mean()),
        'fs_overall_hz':(len(t)-1)/(t[-1]-t[0]),'dt_quantiles_s':dt_q.tolist(),
        'regular_dt_quantiles_s':reg_q.tolist(),'regular_dt_std_s':float(regular.std()),
        'gap_factor':gap_factor,'gap_threshold_s':cutoff,'n_gaps':len(gaps),
        'gap_duration_min_s':float(dt[indices].min()) if len(indices) else None,
        'gap_duration_max_s':float(dt[indices].max()) if len(indices) else None,
        'gap_total_interval_s':float(dt[indices].sum()),
        'gap_excess_total_s':float((dt[indices]-nominal_dt).sum()),
        'n_segments':len(segments),'segment_duration_min_s':float(durations.min()),
        'segment_duration_median_s':float(np.median(durations)),
        'segment_duration_max_s':float(durations.max()),
        'segments_at_least_1s':int((durations>=1).sum()),
        'conservative_window_counts_before_filter':window_counts,
        'axis_mean':np.nanmean(acceleration,axis=0).tolist(),
        'axis_min':np.nanmin(acceleration,axis=0).tolist(),
        'axis_max':np.nanmax(acceleration,axis=0).tolist(),
        'axis_std':np.nanstd(acceleration,axis=0).tolist(),
        'axis_distinct_counts':[int(len(np.unique(acceleration[:,j]))) for j in range(3)],
        'rows_abs_acceleration_ge_3g':int((np.abs(acceleration)>=3*9.80665).any(axis=1).sum()),
        'gap_count_sensitivity':{str(f):int((dt>f*nominal_dt).sum()) for f in [1.25,1.5,2,5,10]},
        'elapsed_seconds':time.perf_counter()-started}
    return stats,gaps,segments,bad_rows

def run_audit(input_dir,output_dir,cache=None):
    input_dir=Path(input_dir);output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    summaries=[];all_gaps=[];all_segments=[];all_bad=[]
    for filename,condition in FILES.items():
        summary,gaps,segments,bad=audit_file(input_dir/filename,condition,cache=cache)
        summaries.append(summary);all_gaps+=gaps;all_segments+=segments;all_bad+=bad
        print(f'{condition}: n={summary["rows_numeric"]}, gaps={summary["n_gaps"]}, '
              f'max_segment={summary["segment_duration_max_s"]:.6f}s',flush=True)
    result={'input_provenance':'User-provided original XLSX attachments; historical download date not recorded here.',
            'units':'Time seconds and acceleration m/s² according to dataset article; headers alone do not independently prove acceleration scale.',
            'environment':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,
                           'openpyxl':openpyxl.__version__},'files':summaries}
    (output_dir/'audit_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    keys=['condition','filename','rows_numeric','columns','duration_s','dt_median_s',
          'fs_regular_mean_hz','fs_overall_hz','n_gaps','gap_duration_min_s','gap_duration_max_s',
          'gap_excess_total_s','n_segments','segment_duration_median_s','segment_duration_max_s',
          'segments_at_least_1s','string_cells_first_four','nonfinite_cells','nonempty_extra_rows','sha256']
    write_csv(output_dir/'inventory.csv',[{k:s[k] for k in keys} for s in summaries])
    write_csv(output_dir/'gaps.csv',all_gaps);write_csv(output_dir/'segments.csv',all_segments)
    if all_bad:write_csv(output_dir/'invalid_cells.csv',all_bad)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('results'))
    parser.add_argument('--cache',type=Path,default=None)
    args=parser.parse_args();run_audit(args.input,args.output,args.cache)
