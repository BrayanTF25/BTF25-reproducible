function BTF25_paso2_completo
% Guardar con este nombre y ejecutar BTF25_paso2_completo.
% Requiere MATLAB con Signal Processing Toolbox. No requiere otros scripts.
inDir=uigetdir(pwd,'Seleccione la carpeta de los CINCO Excel originales');
if isequal(inDir,0),return;end
out=fullfile(inDir,['BTF25_salida_' datestr(now,'yyyymmdd_HHMMSSFFF')]);
mkdir(out);diary(fullfile(out,'ejecucion.txt'));
report=struct('status','started','matlab_executed',true,...
 'matlab_version',version,'release',version('-release'),...
 'products',ver,'step2_closed',false);
try
 assert(~isempty(ver('signal')),'Falta Signal Processing Toolbox.');
 assert(usejava('jvm'),'Se requiere Java habilitado para los hashes SHA-256.');
 source=[mfilename('fullpath') '.m'];
 report.code_sha256=hashbytes(readbytes(source));
 copyfile(source,fullfile(out,'BTF25_paso2_completo.m'));
 report.started_local=datestr(now,31);
 writejson(fullfile(out,'estado.json'),report);
 fprintf('Ejecutando pruebas numericas...\n');
 numerical_tests(out);
 files={'Healthy.xlsx','Damaged Bottom Right Blade.xlsx',...
  'Damaged Top Right Blade.xlsx','Unbalanced Bottom Right Blade.xlsx',...
  'Unbalanced Top Right Blade.xlsx'};
 classes={'Healthy','Damaged_LR','Damaged_UR','Unbalanced_LR','Unbalanced_UR'};
 expectedHashes={...
 '9aee03af22b440bd701a2bf692cc2cf0178c33e1a76b1f41a1c0e06d5c857429',...
 'b638095ebe3cab60eecf0b51ba74f05a09a1d56005aabca0399d14b918e1f933',...
 '737c7084fe656b6d31f3d592737a90ffbb668ae95526ac0b4a0665cdc4d8c70e',...
 '48d9fb396202020a598022b885b513847df1f3a5f43fc2c3459557e2774b6d17',...
 '5997930f36c68e06d785a3abc18fd1ec7ed7b05225f0852ca327131c5ca03a90'};
 devIntervals=[10 70;70 130;130 190;190 250];
 testIntervals=[252 312;312 372];
 cfg=struct('fs_hz',1024,'n_samples',500,'highpass_hz',10,...
  'lowpass_hz',409.6,'butterworth_order',4,'gap_factor',1.5,...
  'numeric_energy_floor',1e-12,'scale_floor',1e-12,...
  'reference_band_hz',[10 100],'comparison_band_hz',[140 200],...
  'development_intervals_s',devIntervals,'test_intervals_s',testIntervals);
 cfg.class_order=classes;writejson(fullfile(out,'config.json'),cfg);
 F=[];M=[];hashes=cell(5,2);
 for c=1:5
  fprintf('Archivo %d/5: %s\n',c,files{c});drawnow;
  path=fullfile(inDir,files{c});assert(isfile(path),'Falta %s',files{c});
  hashes{c,1}=files{c};hashes{c,2}=hashbytes(readbytes(path));
  assert(strcmp(hashes{c,2},expectedHashes{c}),...
   'El archivo %s no coincide con el Excel original de referencia.',files{c});
  C=readcell(path);assert(size(C,2)>=4,'Se requieren cuatro columnas.');
  a=zeros(size(C,1)-1,4);
  for col=1:4
   for row=2:size(C,1)
    x=C{row,col};
    if isnumeric(x)&&isscalar(x),a(row-1,col)=double(x);
    elseif ischar(x)||isstring(x),a(row-1,col)=str2double(x);
    else,error('Celda no valida: fila %d columna %d.',row,col);end
   end
  end
  clear C;
  assert(all(isfinite(a(:)))&&all(diff(a(:,1))>0),'Datos o tiempos no validos.');
  t=a(:,1)-a(1,1);dt=diff(t);
  borders=[1;find(dt>1.5*median(dt))+1;length(t)+1];
  for j=1:length(borders)-1
   b=borders(j);en=borders(j+1)-1;part=0;block=0;
   if en-b+1==500
    for k=1:4
     if t(b)>=devIntervals(k,1)&&t(en)<devIntervals(k,2),part=1;block=k;end
    end
    for k=1:2
     if t(b)>=testIntervals(k,1)&&t(en)<testIntervals(k,2),part=2;block=k;end
    end
   end
   M(end+1,:)=[c-1,j,b,en,t(b),t(en),en-b+1,part,block]; %#ok<AGROW>
   if part>0
    [vr,r,~,et]=extract_features(a(b:en,2:4));
    if et>1e-12
     F(end+1,:)=[c-1,j,block,part,t(b),t(en),vr,r]; %#ok<AGROW>
    end
   end
  end
 end
 names={'class_id','segment_id','block','partition','start_relative_s',...
  'end_relative_s','v_rms','r0','r1','r2','r3','r4','r5'};
 writetable(array2table(F,'VariableNames',names),fullfile(out,'features.csv'));
 writetable(array2table(M,'VariableNames',{'class_id','segment_id','begin_row',...
  'end_row','start_s','end_s','n','partition','block'}),fullfile(out,'manifest.csv'));
 writetable(cell2table(hashes,'VariableNames',{'filename','sha256'}),...
  fullfile(out,'input_hashes.csv'));
 dev=F(F(:,4)==1,:);test=F(F(:,4)==2,:);
 assert(size(F,1)==3386&&size(dev,1)==2256&&size(test,1)==1130,...
  'El numero de fragmentos no coincide con la referencia.');
 assert(size(M,1)==3998,'El numero de tramos no coincide.');
 for c=0:4
  assert(min(test(test(:,1)==c,5))-max(dev(dev(:,1)==c,6))>=2,...
   'Separacion temporal insuficiente.');
 end
 model=fit_model(dev);model.class_order=classes;
 writejson(fullfile(out,'frozen_parameters.json'),model);
 save(fullfile(out,'frozen_model.mat'),'model','cfg');
 P=predict_model(test,model);
 writetable(array2table([test P],'VariableNames',[names,...
  {'score_a','pred_a','pred_b','pred_multiclass','velocity_level','prototype_tie'}]),...
  fullfile(out,'test_predictions.csv'));
 y=double(test(:,1)>0);
 result.a=measure(y,P(:,2),2);result.b=measure(y,P(:,3),2);
 result.multiclass_a=measure(test(:,1),P(:,4),5);
 writejson(fullfile(out,'results.json'),result);
 writematrix(result.a.confusion,fullfile(out,'matriz_binaria_btf25.csv'));
 writematrix(result.b.confusion,fullfile(out,'matriz_binaria_rms.csv'));
 writematrix(result.multiclass_a.confusion,fullfile(out,'matriz_multiclase_btf25.csv'));
 metrics=[result.a;result.b;result.multiclass_a];
 T=table({'BTF25_binario';'RMS_binario';'BTF25_multiclase'},[metrics.n]',...
  [metrics.accuracy]',[metrics.balanced_accuracy]',[metrics.f1_macro]',[metrics.kappa]',...
  'VariableNames',{'metodo','n','exactitud','exactitud_balanceada','f1_macro','kappa'});
 writetable(T,fullfile(out,'metricas_matlab.csv'));disp(T);
 local=compare_embedded(test,P,model);writejson(fullfile(out,'comparacion_local.json'),local);
 report.status='executed_pending_full_comparison';report.local_comparison=local;
 report.finished_local=datestr(now,31);report.step2_closed=false;
 writejson(fullfile(out,'estado.json'),report);
 fprintf('\nEjecucion terminada. La comparacion completa se revisara con los CSV.\n');
 zipName='RESULTADOS_PASO2_PARA_REVISAR.zip';
catch ME
 report.status='failed';report.message=ME.message;report.identifier=ME.identifier;
 writejson(fullfile(out,'estado.json'),report);
 disp(getReport(ME,'extended','hyperlinks','off'));
 zipName='ERROR_PASO2_PARA_REVISAR.zip';
end
fprintf('Carpeta de evidencias: %s\n',out);diary('off');
zipPath=fullfile(inDir,[datestr(now,'yyyymmdd_HHMMSS') '_' zipName]);
listing=dir(out);listing=listing(~[listing.isdir]);
zip(zipPath,{listing.name},out);
fprintf('\nCOMPARTE ESTE ARCHIVO:\n%s\n',zipPath);
end

function [vr,r,e,total,weighted]=extract_features(a)
assert(size(a,2)==3&&all(isfinite(a(:))),'Entrada triaxial no valida.');
N=size(a,1);fs=1024;w=.5-.5*cos(2*pi*(0:N-1)'/N);U=mean(w.^2);
f=(0:floor(N/2))'*fs/N;A=fft((a-mean(a,1)).*w);A=A(1:length(f),:);
g=filter_gain(f);mask=f>=10&f<=409.6;mask(1)=false;
if mod(N,2)==0,mask(end)=false;end
V=zeros(size(A));V(mask,:)=1000*A(mask,:).*g(mask)./(1i*2*pi*f(mask));
psd=abs(V).^2/(fs*sum(w.^2));
if mod(N,2)==0
 psd(2:end-1,:)=2*psd(2:end-1,:);full=[V;conj(V(end-1:-1:2,:))];
else
 psd(2:end,:)=2*psd(2:end,:);full=[V;conj(V(end:-1:2,:))];
end
weighted=real(ifft(full))/sqrt(U);axisEnergy=sum(psd,1)*fs/N;
assert(all(abs(axisEnergy-mean(weighted.^2,1))<=1e-12+1e-11*abs(mean(weighted.^2,1))),...
 'Fallo de Parseval.');
total=sum(axisEnergy);vr=sqrt(total);
e=[sum(psd(f>=10&f<=100,:),1),sum(psd(f>=140&f<=200,:),1)]*fs/N;
r=log10(max(e,1e-12));
end

function g=filter_gain(f)
[zh,ph,kh]=butter(4,10/512,'high');[zl,pl,kl]=butter(4,409.6/512,'low');
[sh,gh]=zp2sos(zh,ph,kh);[sl,gl]=zp2sos(zl,pl,kl);
g=abs((gh*freqz(sh,2*pi*f/1024)).*(gl*freqz(sl,2*pi*f/1024))).^2;
end

function model=fit_model(F)
X=F(:,8:13);healthy=F(:,1)==0;assert(any(healthy),'Falta desarrollo sano.');
model.binary_normalization=robust_fit(X(healthy,:));
z=normalize_features(X(healthy,:),model.binary_normalization);
model.threshold_a=quantile7(max(abs(z),[],2),.95);
model.p95_v=quantile7(F(healthy,7),.95);model.p99_v=quantile7(F(healthy,7),.99);
model.multiclass_normalization=robust_fit(X);
z=normalize_features(X,model.multiclass_normalization);pro=[];
for c=1:4
 blocks=unique(F(F(:,1)==c,3));assert(~isempty(blocks),'Falta una clase.');med=[];
 for k=1:length(blocks)
  med(end+1,:)=median(z(F(:,1)==c&F(:,3)==blocks(k),:),1); %#ok<AGROW>
 end
 pro(c,:)=median(med,1); %#ok<AGROW>
end
model.prototypes=pro;model.fit_count=size(F,1);model.fit_healthy_count=sum(healthy);
end

function M=robust_fit(X)
M.median=median(X,1);s=1.4826*median(abs(X-M.median),1);
for j=1:size(X,2)
 if s(j)<=1e-12,s(j)=(quantile7(X(:,j),.75)-quantile7(X(:,j),.25))/1.349;end
end
M.active=s>1e-12;assert(any(M.active),'Todas las caracteristicas son constantes.');
s(~M.active)=1;M.scale=s;
end
function z=normalize_features(X,M)
z=(X-M.median)./M.scale;z=z(:,M.active);
end
function q=quantile7(x,p)
x=sort(x);assert(~isempty(x),'Cuantil de muestra vacia.');h=1+(length(x)-1)*p;
lo=floor(h);hi=ceil(h);q=x(lo)+(h-lo)*(x(hi)-x(lo));
end
function P=predict_model(F,M)
score=max(abs(normalize_features(F(:,8:13),M.binary_normalization)),[],2);
a=double(score>M.threshold_a);b=double(F(:,7)>M.p95_v);
z=normalize_features(F(:,8:13),M.multiclass_normalization);d=zeros(size(F,1),4);
for c=1:4,d(:,c)=mean((z-M.prototypes(c,:)).^2,2);end
[mind,multi]=min(d,[],2);tie=sum(d==mind,2)>1;multi(a==0)=0;
level=ones(size(a));level(F(:,7)>M.p95_v)=2;level(F(:,7)>M.p99_v)=3;
P=[score,a,b,multi,level,double(tie)];
end
function m=measure(y,p,n)
cm=accumarray([y+1,p+1],1,[n n]);tp=diag(cm);actual=sum(cm,2);pred=sum(cm,1)';
m.n=sum(cm(:));m.confusion=cm;m.accuracy=sum(tp)/m.n;
m.balanced_accuracy=mean(tp./actual);m.f1_macro=mean(2*tp./(actual+pred));
pe=sum(actual.*pred)/m.n^2;m.kappa=(m.accuracy-pe)/(1-pe);
m.recall_by_class=tp./actual;m.precision_by_class=tp./pred;
end

function report=compare_embedded(F,P,M)
% Referencias originales Python. No ajustar el modelo para que coincida.
goldBM=[-1.6961802655297589,-2.889406226514288,-2.8630859685651466,...
 -1.0467387221802833,-1.625813037397114,-1.709597740647559];
goldBS=[.2882681524832413,.1569170365227504,.16951277616689442,...
 .09977652045271002,.10065468866960835,.10212790299597936];
goldMM=[-1.6926405817399013,-2.702397173064915,-2.745394588863589,...
 -1.05499159602192,-1.571467458136994,-1.7027637697245817];
goldMS=[.6509436174910472,.2615107508359426,.2511110010054361,...
 .14280354329010636,.2135571762876427,.15939252055907793];
goldP=[1.0162159974150495,.31432289065732066,.49353364216813955,.299119213617486,1.3509723691041904,.8532424129950972;
 -1.0096647374786762,.4023487410750497,-.22793403466774753,-.043394239106270924,.4568064431340709,.31936372670646207;
 .365735505220579,-.01764185565210126,.6028309310510147,.052724960918365996,-.4101068380887959,-.26780402509337653;
 -.712195328822593,.2980774825811929,-.22398372085498314,.0070252801821386905,-.2893649563347095,-.3165636396092904];
x=[M.threshold_a,M.p95_v,M.p99_v,M.binary_normalization.median,...
 M.binary_normalization.scale,M.multiclass_normalization.median,...
 M.multiclass_normalization.scale,M.prototypes(:)'];
y=[3.336831599644593,.4803740159608717,.5212226405451957,...
 goldBM,goldBS,goldMM,goldMS,goldP(:)'];
err=max(abs(x-y));
rows=sortrows([F(:,1:2),P(:,2:6)],[1 2]);
canonical=sprintf('%d,%d,%d,%d,%d,%d,%d\n',rows');
digest=hashbytes(unicode2native(canonical,'UTF-8'));
expected='d14f163b4a89070f35759fdf61cabd522bd9ea9e427b11b3d3a1e928bc8b67e5';
report.parameters_max_absolute_error=err;report.tolerance=1e-11;
report.decisions_sha256=digest;report.decisions_exact_match=strcmp(digest,expected);
report.active_masks_match=all(M.binary_normalization.active)&&all(M.multiclass_normalization.active);
report.local_checks_passed=isfinite(err)&&err<=1e-11&&report.decisions_exact_match&&report.active_masks_match;
report.full_feature_score_manifest_comparison='pending_review_of_exported_csv';
report.step2_closed=false;disp(report);
end

function numerical_tests(out)
N=500;fs=1024;t=(0:N-1)'/fs;w=.5-.5*cos(2*pi*(0:N-1)'/N);U=mean(w.^2);C={};
C(end+1,:)=check('Hann power',abs(U-.375),1e-14);
C(end+1,:)=check('Hann coherent gain',abs(mean(w)-.5),1e-14);
C(end+1,:)=check('Hann ENBW',abs(fs*sum(w.^2)/sum(w)^2-3.072),1e-12);
x=sin(2*pi*163.84*t);A=fft(x);expected=zeros(N,1);
expected(81)=-1i*N/2;expected(421)=1i*N/2;
C(end+1,:)=check('FFT exact sinusoid',max(abs(A-expected)),1e-9);
f=(0:N/2)'*fs/N;V=zeros(N/2+1,1);V(2:end)=1000*A(2:N/2+1)./(1i*2*pi*f(2:end));V(end)=0;
v=real(ifft([V;conj(V(end-1:-1:2))]));ideal=-1000*cos(2*pi*163.84*t)/(2*pi*163.84);
C(end+1,:)=check('Integration sign phase units',max(abs(v-ideal)),1e-10);
fg=linspace(.1,511.9,4096)';
C(end+1,:)=check('Filter analytic reference',max(abs(filter_gain(fg)-analytic_gain(fg))),1e-8);
a=[sin(2*pi*81.92*t),.7*cos(2*pi*40.96*t),.3*sin(2*pi*159.744*t)];
[vr,~,e]=extract_features(a);
W=exp(-2i*pi*((0:N-1)'*(0:N-1))/N);AD=W*((a-mean(a,1)).*w);AD=AD(1:N/2+1,:);
mask=f>=10&f<=409.6;VD=zeros(size(AD));g=analytic_gain(f(mask));
VD(mask,:)=1000*AD(mask,:).*g./(1i*2*pi*f(mask));
psd=abs(VD).^2/(fs*sum(w.^2));psd(2:end-1,:)=2*psd(2:end-1,:);
er=[sum(psd(f>=10&f<=100,:),1),sum(psd(f>=140&f<=200,:),1)]*fs/N;
C(end+1,:)=check('Independent DFT RMS',abs(sqrt(sum(psd(:))*fs/N)-vr),1e-8);
C(end+1,:)=check('Independent DFT band energies',max(abs(er-e)),1e-8);
[~,~,e3]=extract_features(3*a);C(end+1,:)=check('Amplitude scaling',max(abs(e3-9*e)),1e-8);
[~,~,edc]=extract_features(a+[9.81,-4,2]);C(end+1,:)=check('DC removal',max(abs(edc-e)),1e-8);
vp=extract_features(a(:,[3 1 2]));C(end+1,:)=check('Axis permutation',abs(vp-vr),1e-10);
vz=extract_features(ones(N,3)*9.81);C(end+1,:)=check('Constant input',abs(vz),1e-12);
ao=zeros(N,3);ao(:,1)=sin(2*pi*307.2*t);[~,~,eo,to]=extract_features(ao);
C(end+1,:)=check('Energy outside descriptor bands',double(~(sum(eo)<=1e-12&&to>1e-12)),0);
freqs=[12.288,20.48,40.96,81.92,159.744,163.84,216.67,327.68,399.36,...
 10,10.24,11,15,30,100,140,200,400,409.6];
required=[40.96,81.92,159.744,163.84,216.67,327.68,399.36];S=[];D=[];
for j=1:length(freqs)
 fj=freqs(j);reference=analytic_gain(fj)*1000/(2*pi*fj*sqrt(2));errors=zeros(16,1);
 for k=0:15
  phase=k*2*pi/16;aa=zeros(N,3);aa(:,1)=sin(2*pi*fj*t+phase);
  got=extract_features(aa);errors(k+1)=abs(got/reference-1);
  D(end+1,:)=[fj,phase,reference,got,errors(k+1)]; %#ok<AGROW>
 end
 needed=ismember(fj,required);S(end+1,:)=[fj,100*max(errors),needed]; %#ok<AGROW>
 if needed,C(end+1,:)=check(sprintf('Interior sinus %.3f Hz',fj),max(errors),.01);end
end
m=measure([zeros(4,1);ones(6,1)],[0;0;0;1;0;0;1;1;1;1],2);
C(end+1,:)=check('Binary confusion',max(abs(m.confusion(:)-[3;2;1;4])),0);
C(end+1,:)=check('Binary accuracy',abs(m.accuracy-.7),1e-14);
C(end+1,:)=check('Binary BA',abs(m.balanced_accuracy-17/24),1e-14);
C(end+1,:)=check('Binary F1',abs(m.f1_macro-23/33),1e-14);
C(end+1,:)=check('Binary Kappa',abs(m.kappa-.4),1e-14);
m=measure([zeros(4,1);ones(3,1);2*ones(3,1)],[0;0;0;1;1;1;2;0;2;2],3);
C(end+1,:)=check('Multiclass BA',abs(m.balanced_accuracy-25/36),1e-14);
C(end+1,:)=check('Multiclass F1',abs(m.f1_macro-25/36),1e-14);
C(end+1,:)=check('Multiclass Kappa',abs(m.kappa-6/11),1e-14);
writetable(cell2table(C,'VariableNames',{'name','error','tolerance','passed'}),fullfile(out,'pruebas_numericas.csv'));
writetable(array2table(S,'VariableNames',{'frequency_hz','max_percent_error','required_1_percent'}),fullfile(out,'senos_resumen.csv'));
writetable(array2table(D,'VariableNames',{'frequency_hz','phase_rad','expected_mm_s','computed_mm_s','relative_error'}),fullfile(out,'senos_detalle.csv'));
assert(all(cell2mat(C(:,4))),'Una prueba numerica fallo; revise pruebas_numericas.csv.');
fprintf('Pruebas aprobadas: %d. Casos sinusoidales: %d.\n',size(C,1),size(D,1));
end
function g=analytic_gain(f)
x=tan(pi*f/1024);a=tan(pi*10/1024);b=tan(pi*409.6/1024);
g=(x.^8./(x.^8+a^8)).*(b^8./(b^8+x.^8));
end
function row=check(name,err,tol)
row={name,err,tol,isfinite(err)&&err<=tol};
end
function writejson(path,x)
fid=fopen(path,'w');assert(fid>=0,'No se pudo escribir %s',path);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(x));
end
function bytes=readbytes(path)
fid=fopen(path,'rb');assert(fid>=0,'No se pudo leer %s',path);
cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
end
function h=hashbytes(bytes)
md=java.security.MessageDigest.getInstance('SHA-256');md.update(uint8(bytes(:)));
raw=typecast(md.digest(),'uint8');h=lower(reshape(dec2hex(raw,2)',1,[]));
end
