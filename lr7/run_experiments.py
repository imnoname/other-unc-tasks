"""Run reproducible PSO experiments and create report-ready figures."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys

from PIL import Image, ImageDraw, ImageFont

from pso import ParticleSwarm


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
BLUE = "#2878b5"
RED = "#c43c39"
GREEN = "#2c8c62"
BLACK = "#222222"


def font(size: int):
    return ImageFont.truetype(FONT_PATH, size)


def mean_sd(values):
    return statistics.mean(values), (statistics.stdev(values) if len(values) > 1 else 0.0)


def position_error(position):
    return math.sqrt(sum((x - 5 * i) ** 2 for i, x in enumerate(position, 1)))


def xy_map(x, y, box, limits=(-55.0, 55.0)):
    left, top, right, bottom = box
    low, high = limits
    px = left + (x - low) / (high - low) * (right - left)
    py = bottom - (y - low) / (high - low) * (bottom - top)
    return px, py


def draw_axes(draw, box, limits=(-55, 55), ticks=(-50, -25, 0, 25, 50)):
    left, top, right, bottom = box
    draw.rectangle(box, outline=BLACK, width=2)
    for tick in ticks:
        x, _ = xy_map(tick, limits[0], box, limits)
        _, y = xy_map(limits[0], tick, box, limits)
        draw.line((x, top, x, bottom), fill="#e5e5e5", width=1)
        draw.line((left, y, right, y), fill="#e5e5e5", width=1)
        draw.text((x - 12, bottom + 7), str(tick), fill=BLACK, font=font(15))
        draw.text((left - 39, y - 9), str(tick), fill=BLACK, font=font(15))


def draw_clipped_ellipse(image, box, bounds, color="#75869a", width=1):
    left, top, right, bottom = box
    overlay = Image.new("RGBA", (right-left+1, bottom-top+1), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = bounds
    odraw.ellipse((x0-left, y0-top, x1-left, y1-top), outline=color, width=width)
    image.paste(overlay, (left, top), overlay)


def draw_contour(path: Path, particles, best_position, title="Рой на функции варианта 4"):
    image = Image.new("RGB", (1100, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((250, 20), title, fill=BLACK, font=font(25))
    box = (105, 75, 1010, 690)
    low, high = -55, 55
    # Log-scaled objective background keeps both the basin and the search range visible.
    for py in range(box[1], box[3]):
        y = high - (py - box[1]) / (box[3] - box[1]) * (high - low)
        for px in range(box[0], box[2]):
            x = low + (px - box[0]) / (box[2] - box[0]) * (high - low)
            value = 5 * (x - 5) ** 2 + 10 * (y - 10) ** 2
            shade = min(1.0, math.log10(value + 1) / math.log10(100000))
            image.putpixel((px, py), (int(250 - 75 * shade), int(250 - 80 * shade), int(245 - 45 * shade)))
    draw = ImageDraw.Draw(image)
    draw_axes(draw, box)
    # The exact objective contours are ellipses: 5(x1-5)^2 + 10(x2-10)^2 = level.
    for level in (10, 100, 1000, 10000, 50000):
        rx = math.sqrt(level / 5) / 110 * (box[2] - box[0])
        ry = math.sqrt(level / 10) / 110 * (box[3] - box[1])
        cx, cy = xy_map(5, 10, box)
        draw_clipped_ellipse(image, box, (cx-rx, cy-ry, cx+rx, cy+ry))
        draw = ImageDraw.Draw(image)
    for x, y in particles:
        px, py = xy_map(x, y, box)
        draw.ellipse((px-4, py-4, px+4, py+4), fill=BLUE, outline="white", width=1)
    bx, by = xy_map(best_position[0], best_position[1], box)
    ox, oy = xy_map(5, 10, box)
    draw.line((bx-9, by, bx+9, by), fill=RED, width=3)
    draw.line((bx, by-9, bx, by+9), fill=RED, width=3)
    draw.ellipse((ox-8, oy-8, ox+8, oy+8), outline=GREEN, width=3)
    draw.text((100, 725), "Синий — частицы последнего поколения; красный — найденный минимум; зелёный — точный минимум (5; 10).", fill=BLACK, font=font(18))
    draw.text((520, 760), "x1", fill=BLACK, font=font(18))
    draw.text((35, 370), "x2", fill=BLACK, font=font(18))
    image.save(path)


def draw_surface(path: Path, particles, best_position):
    """Draw a perspective surface and the final two-dimensional swarm with Pillow."""
    image=Image.new("RGB",(1100,800),"white"); draw=ImageDraw.Draw(image)
    draw.text((270,18),"Поверхность функции и частицы последнего поколения",fill=BLACK,font=font(24))
    xmin,xmax=-10.0,20.0; ymin,ymax=-5.0,25.0
    nx=ny=28
    def objective(x,y): return 5*(x-5)**2+10*(y-10)**2
    zmax=objective(xmin,ymin)
    def project(x,y,z):
        u=(x-xmin)/(xmax-xmin); v=(y-ymin)/(ymax-ymin)
        height=190*math.log1p(z)/math.log1p(zmax)
        return 550+(u-v)*350, 475+(u+v)*145-height
    xs=[xmin+(xmax-xmin)*i/nx for i in range(nx+1)]
    ys=[ymin+(ymax-ymin)*j/ny for j in range(ny+1)]
    for order in range(nx+ny,-1,-1):
        for i in range(nx):
            j=order-i
            if not 0<=j<ny: continue
            x0,x1=xs[i],xs[i+1]; y0,y1=ys[j],ys[j+1]
            zvals=[objective(x0,y0),objective(x1,y0),objective(x1,y1),objective(x0,y1)]
            points=[project(x0,y0,zvals[0]),project(x1,y0,zvals[1]),project(x1,y1,zvals[2]),project(x0,y1,zvals[3])]
            shade=sum(math.log1p(z) for z in zvals)/4/math.log1p(zmax)
            color=(int(248-92*shade),int(226-93*shade),int(150+80*shade))
            draw.polygon(points,fill=color,outline="#a9a9a9")
    for x,y in particles:
        if xmin<=x<=xmax and ymin<=y<=ymax:
            px,py=project(x,y,objective(x,y)); draw.ellipse((px-4,py-4,px+4,py+4),fill=BLUE,outline="white")
    ox,oy=project(5,10,0)
    bx,by=project(best_position[0],best_position[1],objective(*best_position))
    draw.ellipse((ox-8,oy-8,ox+8,oy+8),outline=GREEN,width=3)
    draw.line((bx-9,by,bx+9,by),fill=RED,width=3);draw.line((bx,by-9,bx,by+9),fill=RED,width=3)
    # Base axes and labels.
    p00=project(xmin,ymin,0); p10=project(xmax,ymin,0); p01=project(xmin,ymax,0)
    draw.line((p00,p10),fill=BLACK,width=2);draw.line((p00,p01),fill=BLACK,width=2)
    draw.text((p10[0]+10,p10[1]-3),"x1",fill=BLACK,font=font(17))
    draw.text((p01[0]-25,p01[1]+7),"x2",fill=BLACK,font=font(17))
    draw.text((42,740),"Синий — частицы; красный — найденное решение; зелёный — эталонный минимум (5; 10).",fill=BLACK,font=font(18))
    image.save(path)


def draw_snapshots(result, path: Path, chosen):
    image = Image.new("RGB", (1200, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((385, 20), "Пошаговое движение частиц (n = 2)", fill=BLACK, font=font(26))
    panels = [(45, 75, 565, 445), (635, 75, 1155, 445), (45, 500, 565, 870), (635, 500, 1155, 870)]
    for generation, panel in zip(chosen, panels):
        left, top, right, bottom = panel
        box = (left+48, top+45, right-15, bottom-38)
        draw.rectangle(panel, outline="#b0b0b0", width=1)
        draw.text((left+10, top+9), f"Поколение {generation}", fill=BLACK, font=font(19))
        # Elliptical objective contours centered at (5,10).
        draw_axes(draw, box)
        cx, cy = xy_map(5, 10, box)
        for level in (10, 100, 1000, 10000, 50000):
            rx = math.sqrt(level/5)/110*(box[2]-box[0])
            ry = math.sqrt(level/10)/110*(box[3]-box[1])
            draw_clipped_ellipse(image, box, (cx-rx,cy-ry,cx+rx,cy+ry), color="#bdc9d3")
            draw = ImageDraw.Draw(image)
        points = result.snapshots.get(generation, result.snapshots[max(result.snapshots)])
        for point in points:
            x,y=xy_map(point[0],point[1],box)
            draw.ellipse((x-3,y-3,x+3,y+3),fill=BLUE)
    image.save(path)


def draw_line_chart(path: Path, title: str, series, *, y_label: str, x_label: str, log_y=False):
    image = Image.new("RGB", (1100, 680), "white")
    draw = ImageDraw.Draw(image)
    draw.text((260, 20), title, fill=BLACK, font=font(25))
    box=(115,80,1015,555)
    all_y=[max(v,1e-15) for _, ys, _ in series for v in ys]
    y0=min(all_y); y1=max(all_y)
    if log_y:
        lo=math.log10(y0); hi=math.log10(y1)
        if hi-lo < .2: lo-=.1; hi+=.1
        convert=lambda v:(math.log10(max(v,1e-15))-lo)/(hi-lo)
        labels=[10**(lo+(hi-lo)*i/4) for i in range(5)]
        fmt=lambda v:f"{v:.1e}"
    else:
        if y1-y0 < 1e-10: y1=y0+1
        lo=y0; hi=y1
        convert=lambda v:(v-lo)/(hi-lo)
        labels=[lo+(hi-lo)*i/4 for i in range(5)]
        fmt=lambda v:f"{v:.3g}"
    for i,label in enumerate(labels):
        y=box[3]-(box[3]-box[1])*i/4
        draw.line((box[0],y,box[2],y),fill="#dddddd",width=1)
        draw.text((15,y-9),fmt(label),fill=BLACK,font=font(14))
    x_max=max(len(vals) for _,vals,_ in series)
    for name,values,color in series:
        if not values: continue
        points=[]
        for i,value in enumerate(values):
            x=box[0]+(box[2]-box[0])*i/max(1,x_max-1)
            y=box[3]-(box[3]-box[1])*convert(value)
            points.append((x,y))
        if len(points)>1: draw.line(points,fill=color,width=3)
        for x,y in points[::max(1,len(points)//12)]: draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
    draw.rectangle(box,outline=BLACK,width=2)
    for tick in range(5):
        fraction=tick/4
        x=box[0]+(box[2]-box[0])*fraction
        draw.line((x,box[3],x,box[3]+6),fill=BLACK,width=1)
        draw.text((x-18,box[3]+9),str(round((x_max-1)*fraction)),fill=BLACK,font=font(14))
    draw.text((480,595),x_label,fill=BLACK,font=font(18))
    draw.text((22,52),y_label,fill=BLACK,font=font(17))
    legend_x=box[0]
    for name,_,color in series:
        draw.line((legend_x,635,legend_x+28,635),fill=color,width=4)
        draw.text((legend_x+35,624),name,fill=BLACK,font=font(16))
        legend_x+=max(160, len(name)*10)
    image.save(path)


def draw_bars(path: Path, title: str, rows, labels, value_key, color=BLUE, log=False):
    image=Image.new("RGB",(1100,650),"white"); draw=ImageDraw.Draw(image)
    draw.text((310,20),title,fill=BLACK,font=font(24))
    left,top,right,bottom=110,90,1040,540
    vals=[max(float(row[value_key]),1e-15) for row in rows]
    vmax=max(vals)
    vmin=min(vals) if log else 0
    if log:
        lo=math.log10(vmin); hi=math.log10(vmax)
        for k in range(5):
            frac=k/4; y=bottom-(bottom-top)*frac
            draw.line((left,y,right,y),fill="#dddddd",width=1)
            draw.text((15,y-9),f"{10**(lo+(hi-lo)*frac):.1e}",fill=BLACK,font=font(14))
    else:
        for k in range(5):
            y=bottom-(bottom-top)*k/4
            draw.line((left,y,right,y),fill="#dddddd",width=1)
    width=(right-left)/len(rows)*.55
    for i,(row,label,value) in enumerate(zip(rows,labels,vals)):
        x=left+(i+.5)*(right-left)/len(rows)
        if log:
            frac=(math.log10(value)-lo)/max(hi-lo,1e-9)
            y=bottom-frac*(bottom-top)
            draw.line((x-12,y,x+12,y),fill=color,width=4)
            draw.ellipse((x-6,y-6,x+6,y+6),fill=color,outline="white",width=1)
        else:
            frac=value/max(vmax,1e-12)
            y=bottom-frac*(bottom-top)
            draw.rectangle((x-width/2,y,x+width/2,bottom),fill=color)
        draw.text((x-42,bottom+12),label,fill=BLACK,font=font(16))
        draw.text((x-35,y-25),f"{value:.2g}",fill=BLACK,font=font(15))
    draw.rectangle((left,top,right,bottom),outline=BLACK,width=2)
    image.save(path)


def run_one(n, *, particles=60, inertia=.7298, patience=100, tolerance=1e-8, seed=2026, max_generations=1000, capture=()):
    return ParticleSwarm(
        n, particles=particles, max_generations=max_generations, patience=patience,
        inertia=inertia, tolerance=tolerance, seed=seed,
    ).run(capture=capture)


def main(verbose=False):
    # Capture every step in the n=2 demonstration so any iteration can be inspected.
    demo=run_one(2,seed=247,patience=100,max_generations=1000,capture=tuple(range(1001)))
    visible=sorted(demo.snapshots)
    steps=[0, min(10,demo.generations), min(30,demo.generations), demo.generations]
    draw_contour(RESULTS/"function_population.png",demo.snapshots[demo.generations],demo.best_position)
    draw_surface(RESULTS/"surface_population.png",demo.snapshots[demo.generations],demo.best_position)
    draw_snapshots(demo,RESULTS/"search_steps.png",steps)

    dimension_rows=[]
    dimension_histories=[]
    dimension_colors={2:BLUE,3:RED,5:GREEN,10:"#9b59b6"}
    for n in (2,3,5,10):
        runs=[]
        for repeat in range(5):
            result=demo if n==2 and repeat==0 else run_one(n,seed=7000+n*100+repeat)
            runs.append(result)
            dimension_rows.append({"dimensions":n,"repeat":repeat+1,"best_value":result.best_value,
                "position_error":position_error(result.best_position),"generations":result.generations,
                "elapsed_seconds":result.elapsed_seconds,"stop_reason":result.stop_reason})
            if verbose:
                print(f"n={n}, запуск {repeat+1}: f={result.best_value:.4g}, ошибка координат={position_error(result.best_position):.4g}, поколений={result.generations}, время={result.elapsed_seconds:.4f} с")
        dimension_histories.append((f"n={n}",runs[0].best_history,dimension_colors[n]))
    with (RESULTS/"dimension_study.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dimension_rows[0])); writer.writeheader(); writer.writerows(dimension_rows)
    draw_line_chart(RESULTS/"convergence_dimensions.png","Сходимость PSO для разных размерностей",
        dimension_histories,y_label="Лучшее значение f(x)",x_label="Поколение",log_y=True)

    population_rows=[]
    for count in (20,40,80,120):
        runs=[run_one(2,particles=count,seed=8100+count*10+k,patience=80,max_generations=700) for k in range(5)]
        m,sd=mean_sd([r.best_value for r in runs]); tm,ts=mean_sd([r.elapsed_seconds for r in runs])
        gm,gs=mean_sd([r.generations for r in runs])
        population_rows.append({"particles":count,"mean_best":m,"sd_best":sd,"mean_generations":gm,
            "mean_seconds":tm,"sd_seconds":ts,"successes":sum(r.best_value<=1e-8 for r in runs),"runs":len(runs)})

    inertia_rows=[]
    for value in (.4,.7298,.9):
        runs=[run_one(2,inertia=value,seed=9100+int(value*1000)*10+k,patience=80,max_generations=700) for k in range(5)]
        m,sd=mean_sd([r.best_value for r in runs]); tm,ts=mean_sd([r.elapsed_seconds for r in runs])
        gm,gs=mean_sd([r.generations for r in runs])
        inertia_rows.append({"inertia":value,"mean_best":m,"sd_best":sd,"mean_generations":gm,
            "mean_seconds":tm,"sd_seconds":ts,"successes":sum(r.best_value<=1e-8 for r in runs),"runs":len(runs)})

    stopping_rows=[]
    for patience in (30,60,120):
        # Disable the target-value stop so patience alone controls termination.
        runs=[run_one(2,patience=patience,tolerance=0.0,seed=10100+patience*10+k,max_generations=700) for k in range(5)]
        m,sd=mean_sd([r.best_value for r in runs]); tm,ts=mean_sd([r.elapsed_seconds for r in runs])
        gm,gs=mean_sd([r.generations for r in runs])
        stopping_rows.append({"patience":patience,"mean_best":m,"sd_best":sd,"mean_generations":gm,
            "mean_seconds":tm,"sd_seconds":ts,"successes":sum(r.best_value<=1e-8 for r in runs),"runs":len(runs)})

    for filename,rows in (("population_study.csv",population_rows),("inertia_study.csv",inertia_rows),("stopping_study.csv",stopping_rows)):
        with (RESULTS/filename).open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    draw_bars(RESULTS/"population_accuracy.png","Размер роя и среднее лучшее f(x)",population_rows,
        [str(r["particles"]) for r in population_rows],"mean_best",color=BLUE,log=True)
    draw_bars(RESULTS/"inertia_accuracy.png","Инерция и среднее лучшее f(x)",inertia_rows,
        [str(r["inertia"]) for r in inertia_rows],"mean_best",color=GREEN,log=True)
    draw_bars(RESULTS/"stopping_generations.png","Критерий остановки: среднее число поколений",stopping_rows,
        [str(r["patience"]) for r in stopping_rows],"mean_generations",color=RED)

    def aggregate(rows, key):
        result={}
        for n in (2,3,5,10):
            vals=[r[key] for r in rows if r["dimensions"]==n]
            result[str(n)]={"mean":statistics.mean(vals),"sd":statistics.stdev(vals)}
        return result
    summary={
        "variant":4,
        "objective":"sum(5*i*(x_i-5*i)^2), i=1..n",
        "reference_position_1based":[5*i for i in range(1,11)],
        "reference_minimum":0.0,
        "bounds":[-55.0,55.0],
        "interpretation":"The handout prints an unshifted formula but states x_i=5*i and calls the function moved. The experiment uses the shifted formula consistent with the declared minimizer; the chosen bounds are stated in the report.",
        "base_parameters":{"particles":60,"max_generations":1000,"patience":100,"tolerance":1e-8,
          "inertia":.7298,"cognitive":1.49618,"social":1.49618,"velocity_limit_fraction":.2,"seed":247},
        "demo":{"best_position":demo.best_position,"best_value":demo.best_value,"position_error":position_error(demo.best_position),
          "generations":demo.generations,"elapsed_seconds":demo.elapsed_seconds,"stop_reason":demo.stop_reason,
          "best_history":demo.best_history,"mean_history":demo.mean_history,"snapshot_generations":steps,
          "snapshots":{str(g):demo.snapshots[g] for g in steps}},
        "dimension_summary":{"mean_best":aggregate(dimension_rows,"best_value"),
          "mean_position_error":aggregate(dimension_rows,"position_error"),
          "mean_generations":aggregate(dimension_rows,"generations"),
          "mean_seconds":aggregate(dimension_rows,"elapsed_seconds")},
        "dimension_runs":dimension_rows,"population_study":population_rows,
        "inertia_study":inertia_rows,"stopping_study":stopping_rows,
        "notes":{"mutation":"Mutation probability is not a PSO parameter; inertia weight is studied instead.",
          "random":"Uniform random coefficients in [0,1] are used, as in canonical PSO; the handout's mention of normal distribution conflicts with its interval [0,1]."}
    }
    (RESULTS/"results_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")

    print("Лабораторная работа 7 — глобальный PSO, вариант 4")
    print("Цель: f(x)=Σ 5i·(xᵢ−5i)²; эталонный минимум 0 в точке (5,10,…,5n).")
    print("Демонстрационный запуск n=2:")
    print(f"  найдено: x=({demo.best_position[0]:.8f}, {demo.best_position[1]:.8f}), f={demo.best_value:.6g}")
    print(f"  генераций={demo.generations}, время={demo.elapsed_seconds:.4f} с, остановка: {demo.stop_reason}")
    print("\nСравнение размерностей (среднее по 5 запускам):")
    print("  n      f best       ошибка x    поколения   время, с")
    for n in (2,3,5,10):
        key=str(n)
        print(f" {n:>2}  {summary['dimension_summary']['mean_best'][key]['mean']:>12.4g}  {summary['dimension_summary']['mean_position_error'][key]['mean']:>11.4g}  {summary['dimension_summary']['mean_generations'][key]['mean']:>10.1f}  {summary['dimension_summary']['mean_seconds'][key]['mean']:>8.4f}")
    print("\nИсследование числа частиц:")
    for row in population_rows: print(f"  {row['particles']:>3} частиц: f̄={row['mean_best']:.4g} ± {row['sd_best']:.2g}; {row['mean_generations']:.1f} поколений; {row['mean_seconds']:.4f} с; точность достигнута {row['successes']}/{row['runs']}")
    print("\nИсследование инерции:")
    for row in inertia_rows: print(f"  w={row['inertia']:.4g}: f̄={row['mean_best']:.4g} ± {row['sd_best']:.2g}; {row['mean_generations']:.1f} поколений; точность {row['successes']}/{row['runs']}")
    print("\nИсследование остановки:")
    for row in stopping_rows: print(f"  patience={row['patience']}: f̄={row['mean_best']:.4g}; {row['mean_generations']:.1f} поколений; {row['mean_seconds']:.4f} с")
    if verbose:
        print("\nДинамика лучшего результата демонстрационного запуска:")
        for i,value in enumerate(demo.best_history):
            print(f"  поколение {i:4d}: f_best={value:.10g}; f_mean={demo.mean_history[i]:.10g}")
    print("\nГрафики и таблицы записаны в",RESULTS)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser(description="Воспроизводимый эксперимент PSO для лабораторной работы 7")
    parser.add_argument("--verbose",action="store_true",help="вывести историю demo-запуска по поколениям")
    main(parser.parse_args().verbose)
