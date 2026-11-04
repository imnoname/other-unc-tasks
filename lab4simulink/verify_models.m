h=0.01; a=18; p=2; q=4;
for task=1:2
 for disc=0:1
  name=sprintf('lr4_v20_task%d_d%d',task,disc);
  load_system(name);
  s=sim(name,'ReturnWorkspaceOutputs','on');
  z1=s.get('z1'); z2=s.get('z2'); v=[z1.Data(end) z2.Data(end)];
  if task==1
   target=[27 27]; x=[1 3]; N=200;
   if disc, for n=1:N, x=x+h*[x(2),18*x(1)/x(2)]; end, target=x; end
  else
   target=1.5*[exp(6)+exp(-2),exp(6)-exp(-2)]; x=[3 0]; N=100;
   if disc, for n=1:N, x=x+h*[2*x(1)+4*x(2),4*x(1)+2*x(2)]; end, target=x; end
  end
  err=max(abs(v-target)); fprintf('%s: end = %.9f %.9f; max endpoint error = %.3g\n',name,v(1),v(2),err);
  assert(err < 0.001, 'Verification failed');
  close_system(name,0);
 end
end
