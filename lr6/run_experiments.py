"""Run Bayg29 ant-colony experiments for path search and the TSP."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ant_colony import AntColony, route_length, validate_route


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
FONT = r"C:\Windows\Fonts\arial.ttf"

COORDINATES = [
    (1150,1760),(630,1660),(40,2090),(750,1100),(750,2030),(1030,2070),(1650,650),
    (1490,1630),(790,2260),(710,1310),(840,550),(1170,2300),(970,1340),(510,700),
    (750,900),(1280,1200),(230,590),(460,860),(1040,950),(590,1390),(830,1770),
    (490,500),(1840,1240),(1260,1500),(1280,790),(490,2130),(1460,1420),(1260,1910),(360,1980),
]
OPTIMAL_TOUR_1BASED = [1,28,6,12,9,26,3,29,5,21,2,20,10,4,15,18,14,17,22,11,19,25,7,23,8,27,16,13,24]


def distance_matrix(coordinates=COORDINATES):
    return [[math.dist(a, b) for b in coordinates] for a in coordinates]


def format_run(label: str, result, reference: float | None = None) -> str:
    route = [city + 1 for city in result.route]
    text = (f"{label}: длина {'цикла' if result.closed else 'открытого пути'}={result.length:.3f}; "
            f"время={result.elapsed_seconds:.3f} с; маршрут: " + " -> ".join(map(str, route)))
    if result.closed:
        text += f" -> {route[0]}"
    if reference is not None:
        difference = (result.length-reference)/reference*100
        text += f"; контрольное значение={reference:.3f}; разница={difference:+.2f}%"
    return text


def selected_history(history):
    rows = [row for row in history if row["iteration"] == 1 or row["iteration"] % 25 == 0]
    if history and rows[-1]["iteration"] != history[-1]["iteration"]:
        rows.append(history[-1])
    return rows


def draw_route(result, path: Path, title: str):
    canvas = Image.new("RGB", (1100, 760), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 20)
    xs = [point[0] for point in COORDINATES]; ys = [point[1] for point in COORDINATES]
    margin = 70
    def pos(index):
        x, y = COORDINATES[index]
        return (margin + (x-min(xs))/(max(xs)-min(xs))*(1000-2*margin),
                670 - (y-min(ys))/(max(ys)-min(ys))*(600-2*margin))
    edges = list(zip(result.route, result.route[1:]))
    if result.closed:
        edges.append((result.route[-1],result.route[0]))
    for a,b in edges:
        draw.line((*pos(a),*pos(b)), fill="#2878b5", width=3)
    for i in range(len(COORDINATES)):
        x,y=pos(i); draw.ellipse((x-6,y-6,x+6,y+6),fill="#c43c39",outline="white")
        draw.text((x+7,y-13),str(i+1),fill="#222222",font=ImageFont.truetype(FONT,13))
    draw.text((35,20),f"{title}; длина {result.length:.2f}",fill="#111111",font=font)
    canvas.save(path)


def draw_convergence(results, path: Path):
    canvas=Image.new("RGB",(1100,600),"white"); draw=ImageDraw.Draw(canvas)
    box=(125,75,1030,490); draw.rectangle(box,outline="#333333",width=2)
    colors={"path":"#c43c39","cycle":"#2878b5"}
    values=[row["best_length"] for result in results.values() for row in result.history]
    low=min(values); high=max(values)
    small=ImageFont.truetype(FONT,15)
    for tick in range(5):
        fraction=tick/4
        y=box[1]+(box[3]-box[1])*fraction
        value=high-(high-low)*fraction
        draw.line((box[0],y,box[2],y),fill="#dddddd",width=1)
        draw.text((24,y-9),f"{value:.0f}",fill="#333333",font=small)
        x=box[0]+(box[2]-box[0])*fraction
        draw.line((x,box[3],x,box[3]+6),fill="#333333",width=1)
        max_iterations=max(len(result.history) for result in results.values())
        iteration=1+round((max_iterations-1)*fraction)
        draw.text((x-15,box[3]+10),str(iteration),fill="#333333",font=small)
    for label,result in results.items():
        points=[]
        for row in result.history:
            x=box[0]+(box[2]-box[0])*(row["iteration"]-1)/max(1,len(result.history)-1)
            y=box[3]-(box[3]-box[1])*(row["best_length"]-low)/max(high-low,1e-9)
            points.append((x,y))
        draw.line(points,fill=colors[label],width=3)
        legend={"path":"путь","cycle":"цикл TSP"}[label]
        draw.text((850,20+25*list(results).index(label)),legend,fill=colors[label],font=ImageFont.truetype(FONT,18))
    draw.text((125,20),"Сходимость муравьиной колонии",fill="#111111",font=ImageFont.truetype(FONT,22))
    draw.text((480,545),"Итерация",fill="#333333",font=ImageFont.truetype(FONT,17))
    draw.text((24,48),"Длина маршрута",fill="#333333",font=small)
    canvas.save(path)


def main(verbose: bool = False):
    distances=distance_matrix()
    reference_route=[city-1 for city in OPTIMAL_TOUR_1BASED]
    reference_cycle=route_length(reference_route,distances,closed=True)
    reference_open=route_length(reference_route,distances,closed=False)
    base={}
    for label,closed,seed in (("path",False,44),("cycle",True,45)):
        base[label]=AntColony(distances,ants=40,iterations=200,alpha=1.0,beta=3.0,evaporation=.35,seed=seed).run(closed=closed)
        if not validate_route(base[label].route,len(COORDINATES)):
            raise RuntimeError(f"invalid route generated in {label} run")
    draw_route(base["path"],RESULTS/"bayg29_hamiltonian_path.png","Bayg29 — гамильтонов путь (без возврата)")
    draw_route(base["cycle"],RESULTS/"bayg29_tsp_cycle.png","Bayg29 — цикл TSP (с возвратом)")
    draw_convergence(base,RESULTS/"convergence.png")
    study=[]
    for ants,evaporation,seed in ((20,.25,51),(40,.25,52),(20,.45,53),(40,.45,54)):
        result=AntColony(distances,ants=ants,iterations=120,alpha=1.0,beta=3.0,evaporation=evaporation,seed=seed).run(closed=True)
        study.append({"ants":ants,"evaporation":evaporation,"best_length":result.length,"generations":len(result.history),"time_seconds":result.elapsed_seconds,"route":[x+1 for x in result.route]})
    with (RESULTS/"parameter_study.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=["ants","evaporation","best_length","generations","time_seconds","route"]);writer.writeheader()
        for row in study: writer.writerow({**row,"route":" ".join(map(str,row["route"]))})
    summary={"variant":4,"dataset":"Bayg29","coordinates":COORDINATES,"optimal_tour_1based":OPTIMAL_TOUR_1BASED,
             "reference_cycle_length":reference_cycle,"reference_open_path_length":reference_open,
             "path_reference_note":"Removing the closing edge from the known optimal cycle gives a feasible path upper bound, not a proven open-path optimum.",
             "parameters":{"ants":40,"iterations":200,"alpha":1.0,"beta":3.0,"evaporation":.35,"q":100.0},
             "base":{label:{"route_1based":[x+1 for x in result.route],"length":result.length,"closed":result.closed,"elapsed_seconds":result.elapsed_seconds,"history":result.history} for label,result in base.items()},"study":study}
    (RESULTS/"results_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Лабораторная работа 6 — муравьиная колония; вариант 4, Bayg29 (29 городов)")
    print("Расстояния рассчитаны по координатам из методички; формируется полный маршрут по всем городам.")
    print(f"Параметры базовой серии: 40 муравьев, 200 итераций, alpha=1, beta=3, испарение=0.35; режим: {'подробный' if verbose else 'краткий'}.")
    print("\nЧасть 1 — кратчайший гамильтонов путь, без ребра возврата:")
    print("  "+format_run("Найденный путь",base["path"],reference_open))
    print("  Сравнение только с путем, полученным удалением замыкающего ребра известного оптимального тура; это верхняя оценка, не доказанный оптимум пути.")
    print("\nЧасть 2 — задача коммивояжера, замкнутый цикл:")
    print("  "+format_run("Найденный тур",base["cycle"],reference_cycle))
    print("\nКонтрольные итерации лучшего результата:")
    for label,result in base.items():
        print(f"  {label}:")
        rows=result.history if verbose else selected_history(result.history)
        for row in rows:
            print(f"    итерация {row['iteration']:>3}: лучший маршрут={row['best_length']:.3f}; средняя длина={row['mean_length']:.3f}")
    print("\nПараметрическое исследование TSP:")
    print(f"  {'муравьи':>8} {'испарение':>10} {'длина тура':>12} {'итерации':>10} {'время, с':>10}")
    for row in study: print(f"  {row['ants']:>8} {row['evaporation']:>10.2f} {row['best_length']:>12.3f} {row['generations']:>10} {row['time_seconds']:>10.3f}")
    print("\nФайлы результатов:")
    for filename in ("results_summary.json","parameter_study.csv","bayg29_hamiltonian_path.png","bayg29_tsp_cycle.png","convergence.png"):
        print(f"  {RESULTS/filename}")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Муравьиный алгоритм для пути и TSP Bayg29")
    parser.add_argument("--verbose",action="store_true",help="печатать каждую итерацию")
    main(parser.parse_args().verbose)
