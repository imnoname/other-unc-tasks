%% Laboratory work 5, 2026, variant 20: Simulink closed-loop model
% Build the unity-feedback system from the methodical diagram and run K sweep.
clear; clc;
root=fileparts(mfilename('fullpath')); modelDir=fullfile(root,'model');
figDir=fullfile(root,'figures'); resDir=fullfile(root,'results');
if ~exist(modelDir,'dir'),mkdir(modelDir);end
if ~exist(figDir,'dir'),mkdir(figDir);end
if ~exist(resDir,'dir'),mkdir(resDir);end
mdl='lr5_v20_part2'; modelPath=fullfile(modelDir,[mdl '.slx']);
try, bdclose(mdl); catch, end
if exist(modelPath,'file'), delete(modelPath); end
new_system(mdl); open_system(mdl);
set_param(mdl,'StopTime','2','Solver','ode45','RelTol','1e-8','AbsTol','1e-10', ...
    'MaxStep','0.001','ReturnWorkspaceOutputs','on');

% Blocks and their settings (the report repeats this table).
add_block('simulink/Sources/Step',[mdl '/Reference'], ...
    'Time','0','Before','0','After','1','Position',[30 150 65 180]);
add_block('simulink/Math Operations/Sum',[mdl '/Error'], ...
    'Inputs','+-','Position',[120 145 150 185]);
add_block('simulink/Math Operations/Gain',[mdl '/W1'], ...
    'Gain','K1','Position',[205 150 275 180]);
add_block('simulink/Sources/Step',[mdl '/Disturbance'], ...
    'Time','0','Before','0','After','0','Position',[315 55 350 85]);
add_block('simulink/Math Operations/Sum',[mdl '/PlantInput'], ...
    'Inputs','++','Position',[355 145 385 185]);
add_block('simulink/Continuous/Transfer Fcn',[mdl '/W2'], ...
    'Numerator','[1]','Denominator','[0.1 1 1]','Position',[445 150 540 185]);
add_block('simulink/Sinks/Scope',[mdl '/Scope'], ...
    'Position',[640 150 675 185]);
add_block('simulink/Sinks/To Workspace',[mdl '/LogOutput'], ...
    'VariableName','yout','SaveFormat','Timeseries','Position',[600 230 690 260]);

add_line(mdl,'Reference/1','Error/1','autorouting','on');
add_line(mdl,'W2/1','Error/2','autorouting','on');
add_line(mdl,'Error/1','W1/1','autorouting','on');
add_line(mdl,'W1/1','PlantInput/1','autorouting','on');
add_line(mdl,'Disturbance/1','PlantInput/2','autorouting','on');
add_line(mdl,'PlantInput/1','W2/1','autorouting','on');
add_line(mdl,'W2/1','Scope/1','autorouting','on');
add_line(mdl,'W2/1','LogOutput/1','autorouting','on');
set_param(mdl,'ZoomFactor','FitSystem'); save_system(mdl,modelPath);
print(['-s' mdl],'-dpng','-r180',fullfile(figDir,'part2_simulink_scheme.png'));

Kvalues=[9 90 900]; allRuns=struct([]); rows=struct([]);
figure('Visible','off','Color','w','Position',[100 100 1200 700]); hold on; grid on; box on;
colors=lines(numel(Kvalues));
for i=1:numel(Kvalues)
    K=Kvalues(i); assignin('base','K1',K);
    simOut=sim(mdl,'ReturnWorkspaceOutputs','on');
    ts=simOut.get('yout'); t=ts.Time(:); y=ts.Data(:);
    yss=K/(1+K); err=1-y(end);
    [rise10,rise90]=crossing_times(t,y,0.1*yss,0.9*yss);
    outside=find(abs(y-yss)>0.02*abs(yss));
    if isempty(outside), settling=0; else, last=outside(end); if last<numel(t), settling=t(last+1); else, settling=NaN; end, end
    [peak,kpeak]=max(y); overshoot=max(0,100*(peak-yss)/abs(yss));
    poleValues=roots([0.1 1 1+K]);
    wn=sqrt((1+K)/0.1); zeta=1/(2*sqrt(0.1*(1+K)));
    row.K=K; row.final_theory=yss; row.final_sim=y(end); row.static_error=1-yss; row.final_error_sim=err;
    row.overshoot_percent=overshoot; row.peak_time=t(kpeak); row.peak_value=peak;
    row.rise_time_10_90=rise90-rise10; row.settling_time_2percent=settling;
    row.wn=wn; row.zeta=zeta; row.pole_1_real=real(poleValues(1)); row.pole_1_imag=imag(poleValues(1));
    row.pole_2_real=real(poleValues(2)); row.pole_2_imag=imag(poleValues(2));
    if isempty(rows), rows=row; else, rows(i)=row; end %#ok<SAGROW>
    run=struct('K',K,'t',t,'y',y,'yss',yss);
    if isempty(allRuns), allRuns=run; else, allRuns(i)=run; end %#ok<SAGROW>
    plot(t,y,'LineWidth',1.6,'Color',colors(i,:),'DisplayName',sprintf('K = %g',K));
end
plot([0 2],[1 1],'k--','LineWidth',1.0,'DisplayName','Задающее воздействие r(t)=1');
xlabel('Время t, с'); ylabel('Выход y(t)');
title('Переходные характеристики при изменении статического коэффициента W_1');
legend('Location','best'); exportgraphics(gcf,fullfile(figDir,'part2_step_responses.png'),'Resolution',180); close(gcf);
writetable(struct2table(rows),fullfile(resDir,'part2_quality_metrics.csv'));
save(fullfile(resDir,'part2_simulations.mat'),'allRuns','rows','Kvalues');

% Error responses and characteristic roots.
fig=figure('Visible','off','Color','w','Position',[100 100 1250 900]);
tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
for i=1:numel(allRuns)
    nexttile; hold on; grid on; box on;
    plot(allRuns(i).t,1-allRuns(i).y,'LineWidth',1.4,'Color',colors(i,:));
    xlabel('Время t, с'); ylabel('e(t)=r(t)-y(t)'); title(sprintf('Ошибка, K=%g',allRuns(i).K));
end
nexttile; hold on; grid on; box on;
for i=1:numel(Kvalues)
    pr=roots([0.1 1 1+Kvalues(i)]);
    plot(real(pr),imag(pr),'x','MarkerSize',10,'LineWidth',2,'Color',colors(i,:),'DisplayName',sprintf('K=%g',Kvalues(i)));
end
xline(0,'k:'); xlabel('Re(s)'); ylabel('Im(s)'); title('Полюса замкнутой системы'); legend('Location','best');
sgtitle('Ошибки перехода и полюса замкнутой системы');
exportgraphics(fig,fullfile(figDir,'part2_error_poles.png'),'Resolution',180); close(fig);

% Uniform data table for independent plotting/recalculation.
tUniform=(0:0.001:2)'; wide=table(tUniform,'VariableNames',{'time_s'});
for i=1:numel(allRuns)
    wide.(sprintf('y_K_%g',allRuns(i).K))=interp1(allRuns(i).t,allRuns(i).y,tUniform,'pchip');
end
writetable(wide,fullfile(resDir,'part2_responses.csv'));

% Export actual block parameters for the report and reproducibility.
blocks={'Reference','Error','W1','Disturbance','PlantInput','W2','Scope','LogOutput'};
settings=struct([]);
for i=1:numel(blocks)
    path=[mdl '/' blocks{i}]; brow=struct(); brow.block=blocks{i}; brow.block_type=get_param(path,'BlockType');
    brow.position=mat2str(get_param(path,'Position'));
    switch blocks{i}
        case {'Reference','Disturbance'}
            brow.parameters=sprintf('StepTime=%s; InitialValue=%s; FinalValue=%s', ...
                get_param(path,'Time'),get_param(path,'Before'),get_param(path,'After'));
        case 'Error', brow.parameters=['Inputs=' get_param(path,'Inputs')];
        case 'W1', brow.parameters=['Gain=' get_param(path,'Gain')];
        case 'PlantInput', brow.parameters=['Inputs=' get_param(path,'Inputs')];
        case 'W2', brow.parameters=sprintf('Numerator=%s; Denominator=%s',get_param(path,'Numerator'),get_param(path,'Denominator'));
        case 'LogOutput', brow.parameters=sprintf('VariableName=%s; SaveFormat=%s',get_param(path,'VariableName'),get_param(path,'SaveFormat'));
        otherwise, brow.parameters='';
    end
    if isempty(settings), settings=brow; else, settings(i)=brow; end %#ok<SAGROW>
end
writetable(struct2table(settings),fullfile(resDir,'part2_block_settings.csv'));
save_system(mdl,modelPath); close_system(mdl,0);
fprintf('Part 2 complete. Model and experiment results saved in %s\n',root);

function [t10,t90]=crossing_times(t,y,level10,level90)
    i10=find(y>=level10,1,'first'); i90=find(y>=level90,1,'first');
    t10=NaN; t90=NaN;
    if ~isempty(i10)
        if i10==1, t10=t(1); else, t10=interp1(y(i10-1:i10),t(i10-1:i10),level10); end
    end
    if ~isempty(i90)
        if i90==1, t90=t(1); else, t90=interp1(y(i90-1:i90),t(i90-1:i90),level90); end
    end
end
