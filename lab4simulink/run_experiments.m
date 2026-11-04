% Variant 20: reproduce results from the four Simulink models.
clear; close all; clc;
outdir=fullfile(pwd,'figures'); if ~exist(outdir,'dir'), mkdir(outdir); end
file=fopen('results.csv','w'); fprintf(file,'task,h,max_error_1,max_error_2,final_1,final_2\n');
for task=1:2
 names={sprintf('lr4_v20_task%d_d0',task),sprintf('lr4_v20_task%d_d1',task)};
 for j=1:2
  load_system(names{j});
  print(['-s' names{j}],'-dpng','-r150',fullfile(outdir,sprintf('schema_%d_%d.png',task,j-1)));
 end
 if task==1, t0=5; T=7; labels={'y','v = dy/dt'}; else, t0=0; T=1; labels={'x','y'}; end
 continuous=sim(names{1},'ReturnWorkspaceOutputs','on');
 c1=continuous.get('z1'); c2=continuous.get('z2');
 fig=figure('Visible','off','Position',[100 100 1200 850]);
 subplot(2,2,1); plot(c1.Time,c1.Data,'b',c2.Time,c2.Data,'r','LineWidth',1.4); grid on; xlabel('t'); ylabel('state'); title('Continuous solution'); legend(labels,'Location','best');
 subplot(2,2,2); plot(c1.Data,c2.Data,'b','LineWidth',1.4); hold on; plot(c1.Data(1),c2.Data(1),'go','MarkerFaceColor','g'); plot(c1.Data(end),c2.Data(end),'rx','LineWidth',2); grid on; xlabel(labels{1}); ylabel(labels{2}); title('Continuous phase portrait'); legend('trajectory','start','end','Location','best');
 subplot(2,2,3); plot(c1.Time,c1.Data,'k--','LineWidth',1.3); hold on; grid on; xlabel('t'); ylabel(labels{1}); title('Continuous and discrete');
 subplot(2,2,4); hold on; grid on; xlabel(labels{1}); ylabel(labels{2}); title('Discrete phase portraits');
 hs=[0.1 0.05 0.01];
 for k=1:numel(hs)
  h=hs(k); s=Simulink.SimulationInput(names{2}); s=s.setModelParameter('InitFcn',sprintf('h=%.17g; a=18; p=2; q=4;',h));
  o=sim(s); d1=o.get('z1'); d2=o.get('z2'); t=d1.Time;
  if task==1, exact1=(t-4).^3; exact2=3*(t-4).^2; else, exact1=1.5*(exp(6*t)+exp(-2*t)); exact2=1.5*(exp(6*t)-exp(-2*t)); end
  e1=max(abs(d1.Data-exact1)); e2=max(abs(d2.Data-exact2)); fprintf(file,'%d,%.3f,%.12g,%.12g,%.12g,%.12g\n',task,h,e1,e2,d1.Data(end),d2.Data(end));
  subplot(2,2,3); plot(t,d1.Data,'DisplayName',sprintf('h=%.2g',h));
  subplot(2,2,4); plot(d1.Data,d2.Data,'DisplayName',sprintf('h=%.2g',h)); plot(d1.Data(1),d2.Data(1),'go','HandleVisibility','off'); plot(d1.Data(end),d2.Data(end),'rx','HandleVisibility','off');
 end
 subplot(2,2,3); legend('continuous','h=0.1','h=0.05','h=0.01','Location','best'); subplot(2,2,4); legend('Location','best');
 saveas(fig,fullfile(outdir,sprintf('results_%d.png',task))); close(fig);
 fig=figure('Visible','off','Position',[100 100 1200 500]);
 for component=1:2
  subplot(1,2,component); hold on; grid on;
  if component==1, base=c1; else, base=c2; end
  plot(base.Time,base.Data,'k--','DisplayName','continuous');
  for kk=1:numel(hs)
   hh=hs(kk); s=Simulink.SimulationInput(names{2}); s=s.setModelParameter('InitFcn',sprintf('h=%.17g; a=18; p=2; q=4;',hh)); o=sim(s); zz=o.get(sprintf('z%d',component));
   stairs(zz.Time,zz.Data,'DisplayName',sprintf('h=%.2g',hh));
  end
  xlabel('t'); ylabel(labels{component}); title('Continuous and discrete state'); legend('Location','best');
 end
 saveas(fig,fullfile(outdir,sprintf('states_%d.png',task))); close(fig);
 fig=figure('Visible','off','Position',[100 100 1200 500]); subplot(1,2,1); hold on; grid on;
 if task==1, values=[12 18 24]; else, values=[2 4 6]; end
 for k=1:3
  if task==1, init=sprintf('h=0.01; a=%g; p=2; q=4;',values(k)); else, init=sprintf('h=0.01; a=18; p=2; q=%g;',values(k)); end
  s=Simulink.SimulationInput(names{1}); s=s.setModelParameter('InitFcn',init); o=sim(s); z=o.get('z1'); plot(z.Time,z.Data,'DisplayName',sprintf('parameter=%g',values(k)));
 end
 xlabel('t'); ylabel(labels{1}); title('Equation parameter'); legend('Location','best');
 subplot(1,2,2); hold on; grid on;
 methods={'ode23','ode45'}; tolerances={'1e-3','1e-6','1e-9'};
 for k=1:2
  for j=1:3
   s=Simulink.SimulationInput(names{1}); s=s.setModelParameter('Solver',methods{k},'RelTol',tolerances{j},'AbsTol',tolerances{j}); o=sim(s); z=o.get('z1');
   if task==1, ref=(z.Time-4).^3; else, ref=1.5*(exp(6*z.Time)+exp(-2*z.Time)); end
   semilogy(z.Time,max(abs(z.Data-ref),1e-15),'DisplayName',sprintf('%s tol=%s',methods{k},tolerances{j}));
  end
 end
 set(gca,'YScale','log'); xlabel('t'); ylabel('absolute error'); title('Solver and tolerance'); legend('Location','best');
 saveas(fig,fullfile(outdir,sprintf('comparison_%d.png',task))); close(fig);
 for j=1:2, close_system(names{j},0); end
end
fclose(file); disp('ALL SIMULINK EXPERIMENTS COMPLETED');
