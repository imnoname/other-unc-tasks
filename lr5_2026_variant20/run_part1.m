%% Laboratory work 5, 2026, variant 20: nonlinear population model
% Reproducible fixed-step RK4 experiments with 2/15 significant-digit
% quantization, prescribed delta sweep, control, and T1 sensitivity.
clear; clc;
root = fileparts(mfilename('fullpath'));
figDir = fullfile(root,'figures'); resDir = fullfile(root,'results');
if ~exist(figDir,'dir'), mkdir(figDir); end
if ~exist(resDir,'dir'), mkdir(resDir); end

P.a = 1; P.lambda = 1; P.epsilon = 0.01; P.alpha = 0.4;
P.rho = 1; P.T = 1;
P.x10 = 6; P.x20 = 4;
P.h = 0.1; P.tEnd = 200;
deltas = [0.1, 0.130881, 0.15, 0.196565];
precisions = [2, 15];

runs = struct([]); summary = struct([]); idx = 0;
for id = 1:numel(deltas)
    delta = deltas(id);
    for ip = 1:numel(precisions)
        prec = precisions(ip);
        for ctl = 0:1
            idx = idx + 1;
            run = integrate_population(delta,P,logical(ctl),P.T,prec);
            run.delta = delta; run.precision = prec; run.controlled = logical(ctl);
            if idx==1, runs=run; else, runs(idx) = run; end %#ok<SAGROW>
            row.delta = delta; row.precision_digits = prec; row.controlled = logical(ctl);
            row.h = P.h; row.t_end = P.tEnd;
            row.x1_final = run.x1(end); row.x2_final = run.x2(end);
            row.psi_final = run.psi(end); row.u_rms = sqrt(mean(run.u.^2));
            row.x1_min = min(run.x1); row.x1_max = max(run.x1);
            row.x2_min = min(run.x2); row.x2_max = max(run.x2);
            if isempty(summary), summary=row; else, summary(end+1)=row; end %#ok<SAGROW>
        end
    end
end
writetable(struct2table(summary), fullfile(resDir,'part1_summary.csv'));
save(fullfile(resDir,'part1_runs.mat'),'runs','P','deltas','precisions');

% Compare precision in phase space: same step, state, parameters, and delta.
fig = figure('Visible','off','Color','w','Position',[80 80 1400 950]);
tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
for id=1:numel(deltas)
    delta=deltas(id); nexttile; hold on; grid on; box on;
    r2u=find_run(runs,delta,2,false); r15u=find_run(runs,delta,15,false);
    r2c=find_run(runs,delta,2,true);  r15c=find_run(runs,delta,15,true);
    plot(r15u.x1,r15u.x2,'Color',[0.05 0.35 0.75],'LineWidth',1.25,'DisplayName','Без управления, 15 знаков');
    plot(r2u.x1,r2u.x2,'--','Color',[0.55 0.70 0.95],'LineWidth',1.0,'DisplayName','Без управления, 2 знака');
    plot(r15c.x1,r15c.x2,'Color',[0.80 0.15 0.12],'LineWidth',1.25,'DisplayName','С управлением, 15 знаков');
    plot(r2c.x1,r2c.x2,'--','Color',[0.95 0.60 0.55],'LineWidth',1.0,'DisplayName','С управлением, 2 знака');
    plot(P.x10,P.x20,'ko','MarkerFaceColor','k','DisplayName','Начальная точка');
    xlabel('x_1 — плотность жертв'); ylabel('x_2 — плотность хищников');
    title(sprintf('Фазовые траектории, delta = %.6g',delta));
    if id==1, legend('Location','best','FontSize',8); end
end
sgtitle('Влияние управления и точности арифметики на фазовые траектории');
exportgraphics(fig,fullfile(figDir,'part1_phase_precision_control.png'),'Resolution',180); close(fig);

% Time histories, 15 significant digits, all prescribed delta values.
fig=figure('Visible','off','Color','w','Position',[80 80 1400 950]);
tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
for id=1:numel(deltas)
    delta=deltas(id); nexttile; hold on; grid on; box on;
    u=find_run(runs,delta,15,false); c=find_run(runs,delta,15,true);
    plot(u.t,u.x1,'Color',[0.05 0.35 0.75],'LineWidth',1.1,'DisplayName','x_1, без управления');
    plot(u.t,u.x2,'--','Color',[0.05 0.35 0.75],'LineWidth',1.1,'DisplayName','x_2, без управления');
    plot(c.t,c.x1,'Color',[0.80 0.15 0.12],'LineWidth',1.1,'DisplayName','x_1, с управлением');
    plot(c.t,c.x2,'--','Color',[0.80 0.15 0.12],'LineWidth',1.1,'DisplayName','x_2, с управлением');
    xlabel('Время t'); ylabel('Плотность популяции');
    title(sprintf('delta = %.6g',delta));
    if id==1, legend('Location','best','FontSize',8); end
end
sgtitle('Временные зависимости популяций для всех значений \delta');
exportgraphics(fig,fullfile(figDir,'part1_time_delta_control.png'),'Resolution',180); close(fig);

% T sensitivity for the macrovariable and control action at delta=0.1.
Tvalues=[0.5 1 2]; delta=Tvalues(1)*0+0.1; Trows=struct([]);
fig=figure('Visible','off','Color','w','Position',[100 100 1250 480]);
tiledlayout(1,2,'Padding','compact','TileSpacing','compact');
nexttile; hold on; grid on; box on;
nexttile; hold on; grid on; box on;
for k=1:numel(Tvalues)
    run=integrate_population(delta,P,true,Tvalues(k),15);
    nexttile(1); plot(run.t,run.psi,'LineWidth',1.4,'DisplayName',sprintf('T = %.1f',Tvalues(k)));
    nexttile(2); plot(run.t,run.u,'LineWidth',1.2,'DisplayName',sprintf('T = %.1f',Tvalues(k)));
    row=struct(); row.T=Tvalues(k); row.J_macro=0.5*(P.x10-P.rho*P.x20)^2*(Tvalues(k)+1/Tvalues(k));
    row.control_energy=trapz(run.t,run.u.^2); row.psi_2percent_time=Tvalues(k)*log(50);
    row.psi_final=run.psi(end); if isempty(Trows), Trows=row; else, Trows(end+1)=row; end %#ok<SAGROW>
end
nexttile(1); xlabel('Время t'); ylabel('\psi(t)=x_1-\rho x_2'); title('Сходимость целевой макропеременной'); legend('Location','best');
nexttile(2); xlabel('Время t'); ylabel('u_1(t)'); title('Управляющее воздействие'); legend('Location','best');
exportgraphics(fig,fullfile(figDir,'part1_T_sensitivity.png'),'Resolution',180); close(fig);
writetable(struct2table(Trows),fullfile(resDir,'part1_T_sensitivity.csv'));

% Step-size sensitivity: four fixed-step RK4 runs around the nearly merging
% equilibria at delta=0.130881, for controlled and uncontrolled dynamics.
stepValues=[0.2 0.1 0.05 0.025]; stepRows=struct([]); stepFig=figure('Visible','off','Color','w','Position',[100 100 1200 500]);
tiledlayout(1,2,'Padding','compact','TileSpacing','compact');
for ctl=0:1
    nexttile; hold on; grid on; box on;
    for k=1:numel(stepValues)
        Ps=P; Ps.h=stepValues(k); Ps.tEnd=100;
        r=integrate_population(0.130881,Ps,logical(ctl),P.T,15);
        plot(r.x1,r.x2,'LineWidth',1.15,'DisplayName',sprintf('h = %.3g',stepValues(k)));
        row=struct(); row.controlled=logical(ctl); row.h=Ps.h; row.t_end=Ps.tEnd;
        row.x1_final=r.x1(end); row.x2_final=r.x2(end); row.psi_final=r.psi(end);
        if isempty(stepRows), stepRows=row; else, stepRows(end+1)=row; end %#ok<SAGROW>
    end
    xlabel('x_1'); ylabel('x_2'); title(ternary(ctl,'С управлением','Без управления'));
    legend('Location','best');
end
sgtitle('Чувствительность фазового портрета к шагу RK4, \delta=0.130881');
exportgraphics(stepFig,fullfile(figDir,'part1_step_sensitivity.png'),'Resolution',180); close(stepFig);
writetable(struct2table(stepRows),fullfile(resDir,'part1_step_sensitivity.csv'));

% Initial-condition sensitivity for delta=0.15; chosen points span different
% initial population scales while keeping the predator/prey ratio variable.
initials=[3 2; 6 4; 12 8]; icRows=struct([]);
icFig=figure('Visible','off','Color','w','Position',[100 100 1200 500]); tiledlayout(1,2,'Padding','compact','TileSpacing','compact');
for ctl=0:1
    nexttile; hold on; grid on; box on;
    for k=1:size(initials,1)
        Pi=P; Pi.x10=initials(k,1); Pi.x20=initials(k,2); Pi.tEnd=100;
        r=integrate_population(0.15,Pi,logical(ctl),P.T,15);
        plot(r.x1,r.x2,'LineWidth',1.25,'DisplayName',sprintf('(%.0f, %.0f)',Pi.x10,Pi.x20));
        row=struct(); row.controlled=logical(ctl); row.x10=Pi.x10; row.x20=Pi.x20; row.x1_final=r.x1(end); row.x2_final=r.x2(end); row.psi_final=r.psi(end);
        if isempty(icRows), icRows=row; else, icRows(end+1)=row; end %#ok<SAGROW>
    end
    xlabel('x_1'); ylabel('x_2'); title(ternary(ctl,'С управлением','Без управления'));
    legend('Location','best');
end
sgtitle('Влияние начального состояния, \delta=0.15');
exportgraphics(icFig,fullfile(figDir,'part1_initial_conditions.png'),'Resolution',180); close(icFig);
writetable(struct2table(icRows),fullfile(resDir,'part1_initial_condition_sensitivity.csv'));

% Positive equilibria and local linear stability.  Substitution of the
% second nullcline reduces the nonzero fixed points to a cubic in x1.
eqRows=struct([]); bifFig=figure('Visible','off','Color','w','Position',[100 100 1000 620]); hold on; grid on; box on;
for id=1:numel(deltas)
    delta=deltas(id); rr=roots([4*delta, -380*delta, 1500-1975*delta, -2500*delta-2500]);
    rr=real(rr(abs(imag(rr))<1e-8));
    for k=1:numel(rr)
        x=rr(k); y=(x/(1+P.alpha*x)-1)/delta;
        if x<=0 || y<=0, continue; end
        den=1+P.alpha*x; dpdx=y/den^2; dpdy=x/den;
        J=[P.a-dpdx-2*P.epsilon*x, -dpdy; dpdx, -P.lambda+dpdy-2*delta*y];
        ev=eig(J); stable=all(real(ev)<0); saddle=prod(real(ev))<0;
        row=struct(); row.delta=delta; row.x1=x; row.x2=y; row.eigen_1_real=real(ev(1)); row.eigen_1_imag=imag(ev(1)); row.eigen_2_real=real(ev(2)); row.eigen_2_imag=imag(ev(2));
        if saddle, row.classification='saddle'; elseif stable && any(abs(imag(ev))>1e-8), row.classification='stable focus'; elseif stable, row.classification='stable node'; elseif all(real(ev)>0) && any(abs(imag(ev))>1e-8), row.classification='unstable focus'; elseif all(real(ev)>0), row.classification='unstable node'; else, row.classification='unstable'; end
        if isempty(eqRows), eqRows=row; else, eqRows(end+1)=row; end %#ok<SAGROW>
        if stable, plot(delta,x,'bo','MarkerFaceColor','b','MarkerSize',7); else, plot(delta,x,'ro','MarkerFaceColor','w','MarkerSize',7); end
    end
end
xlabel('\delta'); ylabel('Равновесное x_1^*'); title('Положительные равновесия популяционной модели');
hStable=plot(nan,nan,'bo','MarkerFaceColor','b','MarkerSize',7);
hOther=plot(nan,nan,'ro','MarkerFaceColor','w','MarkerSize',7);
legend([hStable hOther],{'Устойчивое','Неустойчивое или седло'},'Location','best');
exportgraphics(bifFig,fullfile(figDir,'part1_equilibria.png'),'Resolution',180); close(bifFig);
writetable(struct2table(eqRows),fullfile(resDir,'part1_equilibria.csv'));

fprintf('Part 1 complete. Wrote %d runs and figures to %s\n',numel(runs),root);

function run=integrate_population(delta,P,controlled,T,prec)
    h=round_sig(P.h,prec); N=round(P.tEnd/h); t=(0:N)'*h;
    x1=zeros(N+1,1); x2=x1; psi=x1; u=x1;
    x1(1)=round_sig(P.x10,prec); x2(1)=round_sig(P.x20,prec);
    a=round_sig(P.a,prec); lam=round_sig(P.lambda,prec);
    epsv=round_sig(P.epsilon,prec); alpha=round_sig(P.alpha,prec);
    rho=round_sig(P.rho,prec); delta=round_sig(delta,prec); T=round_sig(T,prec);
    for k=1:N
        [k1x,k1y]=rhs(x1(k),x2(k),a,lam,epsv,alpha,delta,rho,T,controlled,prec);
        xa=round_sig(x1(k)+h*k1x/2,prec); ya=round_sig(x2(k)+h*k1y/2,prec);
        [k2x,k2y]=rhs(xa,ya,a,lam,epsv,alpha,delta,rho,T,controlled,prec);
        xb=round_sig(x1(k)+h*k2x/2,prec); yb=round_sig(x2(k)+h*k2y/2,prec);
        [k3x,k3y]=rhs(xb,yb,a,lam,epsv,alpha,delta,rho,T,controlled,prec);
        xc=round_sig(x1(k)+h*k3x,prec); yc=round_sig(x2(k)+h*k3y,prec);
        [k4x,k4y]=rhs(xc,yc,a,lam,epsv,alpha,delta,rho,T,controlled,prec);
        x1(k+1)=round_sig(x1(k)+h*(k1x+2*k2x+2*k3x+k4x)/6,prec);
        x2(k+1)=round_sig(x2(k)+h*(k1y+2*k2y+2*k3y+k4y)/6,prec);
    end
    for k=1:N+1
        [~,~,u(k),psi(k)]=rhs(x1(k),x2(k),a,lam,epsv,alpha,delta,rho,T,controlled,prec);
    end
    run=struct('t',t,'x1',x1,'x2',x2,'psi',psi,'u',u);
end

function [dx1,dx2,u,psi]=rhs(x1,x2,a,lam,epsv,alpha,delta,rho,T,controlled,prec)
    p=round_sig(x1*x2/(1+alpha*x1),prec);
    f1=round_sig(a*x1-p-epsv*x1^2,prec);
    f2=round_sig(-lam*x2+p-delta*x2^2,prec);
    psi=round_sig(x1-rho*x2,prec);
    if controlled
        u=round_sig(-psi/T-f1+rho*f2,prec);
    else
        u=0;
    end
    dx1=round_sig(f1+u,prec); dx2=f2;
end

function y=round_sig(x,n)
    if n>=15 || x==0 || ~isfinite(x), y=x; return; end
    y=round(x,n-1-floor(log10(abs(x))));
end

function run=find_run(runs,delta,precision,controlled)
    mask=([runs.delta]==delta) & ([runs.precision]==precision) & ([runs.controlled]==controlled);
    run=runs(find(mask,1));
end

function label=ternary(flag,a,b)
    if flag, label=a; else, label=b; end
end
