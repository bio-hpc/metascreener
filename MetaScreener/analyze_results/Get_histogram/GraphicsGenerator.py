#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Generate all graphics of get_histogram
# ______________________________________________________________________________________________________________________
import matplotlib
matplotlib.use('Agg')
from pylab import *
from debug import BColors

TAG = "GrahpicsGenerator.py" 
color = BColors.GREEN
FORMAT_SVG = "svg"
FORMAT_PNG = "png"
DPI = 300


class GraphicsGenerator(object):

    def generate_global_graph(self, leyenda, datos, clrs, name_lig, out_put):
        mas_menos_graph = 0.5
        ind = np.arange(1)  # the x locations for the groups
        width = 0.1       # the width of the bars
        fig, ax = plt.subplots()
        for i in np.arange(0, len(datos)):
            ax.bar(ind + i * width, float(datos[i]), width, color=clrs[i])

        ax.set_ylim(min(np.array(datos, dtype=float))
                    - mas_menos_graph, max(np.array(datos, dtype=float)) + mas_menos_graph)
        ax.set_ylabel('Contribution (kcal/mol)')
        ax.set_title(name_lig+'\nEnergetic contributions to binding energy ')
        xmax = 1+float(len(datos))/10
        ax.set_xlim(-1, xmax)

        ax.axhline(y=0, xmin=-1, xmax=xmax, linewidth=0.2, color='k')
        ax.set_xticklabels("")

        self.put_legend(ax, leyenda, clrs)
        self.save_graph(fig, out_put)
        
    @staticmethod
    def remove_zero_values(data_aux, type_atom_aux):
        datos = []
        type_atom = []
        for row in range(len(data_aux)):
            show_score = False
            for i in data_aux[row]:
                if i != 0:
                    show_score = True
            if show_score:
                datos.append(data_aux[row])
                type_atom.append(type_atom_aux[row])
        return datos, type_atom
    
    def generate_atom_graph(self, leyenda, datos, type_atom, clrs, name_lig, out_put):
        datos, type_atom = self.remove_zero_values(datos, type_atom)
        fig, ax = plt.subplots()
        if len(datos) > 0:
            ind = np.arange(len(datos))
            width = 0.1
            
            ax.set_ylabel('Contribution (kcal/mol)')
            ax.set_title(name_lig+'\nEnergetic contributions to binding energy ')
            ax.axhline(y=0, xmin=-1, xmax=len(datos[0]), linewidth=0.2, color='k')
            mini = []
            maxi = []
            tam_linea_borde_bar = [0.1]

            for i in np.arange(len(datos[0])):
                mini.append(min(np.array([row[i] for row in datos], dtype=float)))
                maxi.append(max(np.array([row[i] for row in datos], dtype=float)))
                ax.bar((ind+(width*i)) - (width*len(datos[0])) / 2, np.array([row[i] for row in datos], dtype=float),
                       width, color=clrs[i], linewidth=tam_linea_borde_bar)
            ax.set_xlim(-1, len(datos))
            ax.set_xticks(ind)
            ax.set_xticklabels(type_atom)
            ax.set_ylim(min(mini)-0.3, max(maxi)+0.3)

            self.put_legend(ax, leyenda, clrs)
            fig.gca().xaxis.grid(True, linewidth=0.3)
            self.rotate_ticks_x(45, ax)
        self.save_graph(fig, out_put)

    def generate_best_pose_join_graph(self, leyenda, datos, nom_ligs, clrs, out_put):
        ind = np.arange(len(datos))
        width = 0.1
        fig, ax = plt.subplots()
        ax.axhline(y=0, xmin=-1, xmax=len(datos[0]), linewidth=0.2, color='k')
        mini = []
        maxi = []
        count = 0
        tam_linea_borde_bar = [0.01]

        for i in np.arange(len(datos[0])):
            mini.append(min(np.array([row[i] for row in datos], dtype=float)))
            maxi.append(max(np.array([row[i] for row in datos], dtype=float)))
            ax.bar((ind-0.5) + (width*count), np.array([row[i] for row in datos], dtype=float), width, color=clrs[i],
                   linewidth=tam_linea_borde_bar)
            count += 1
        ax.set_xlim(-1, len(datos))
        ax.set_xticks(ind)
        ax.set_xticklabels(nom_ligs)
        ax.set_ylim(min(mini)-0.3, max(maxi)+1.5)
        self.put_legend(ax, leyenda, clrs)
        self.rotate_ticks_x(45, ax)

        ax.set_xlabel('Docked pose #')
        ax.set_ylabel('Contribution (kcal/mol)')
        ax.set_title('Energetic contributions to binding energy -- summary')
        self.save_graph(fig, out_put)

    def generate_histogram(self, data, title, x_label, y_label, y_scale, x_label_rotate, out_put):
        if len(data) > 1:
            fig, ax = plt.subplots()
            n, bins = np.histogram(data, 50)
            ax.hist(data, bins=50, alpha=0.5, facecolor='red')
            left = np.array(bins[:-1])
            right = np.array(bins[1:])
            ax.set_xlim(left[0] - 0.5, right[-1] + 0.5)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            if y_scale!="":
                ax.set_yscale(y_scale) 
            ax.set_title(title)
            for tick in ax.xaxis.get_major_ticks():
                # tick.label.set_fontsize(6)
                tick.label.set_rotation(x_label_rotate)
            self.save_graph(fig, out_put)
        else:

            print("Error: GraphicsGenerator:generate_histogram: Only one molecule: len(data): "+str(len(data)))

    def generate_histogram_2(self, data_1, data_2, label_1, label_2, title, x_label,y_label, y_scale, out_put):
        fig, ax = plt.subplots()
        ax.hist(data_1, bins=50, alpha=1.0, label=label_1, facecolor='blue')
        ax.hist(data_2, bins=50, alpha=0.5, label=label_2, facecolor='red')

        ax.set_xlim(min(data_2) - 0.5, max(data_1) + 0.5)
        ax.plot([0, 1, 2], [10, 10, 100], marker='o', linestyle='-')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_yscale(y_scale)
        ax.set_title(title)

        # eliminar ticks

        ax.tick_params(
            axis='x',             # changes apply to the x-axis
            bottom=True,          # ticks along the bottom edge are off
            top=False)            # ticks along the top edge are off

        ax.tick_params(
            axis='y',             # changes apply to the x-axis
            which='both',         # both major and minor ticks are affected
            left=True,            # ticks along the bottom edge are off
            right=False)          # ticks along the top edge are off

        ax.legend(loc='upper right', prop={'size': 6})

        self.save_graph(fig, out_put)

    def generate_histogram_poseview(self, data, lbls, title, y_label,  out_put):
        if data and len(data)>0:
            fig, ax = plt.subplots()
            ind = np.arange(len(lbls))
            width = .35
            ax.bar(ind, data, width=width)
            ax.set_xlim(-0.5, len(lbls) + 0.5)
            ax.set_ylim(min(data) - 0.5, max(data) + 0.5)

            ax.axhline(y=0, xmin=-0.5, xmax=len(lbls) + 0.5, linewidth=0.2, color='k')
            ax.set_ylabel(y_label)
            ax.set_title(title)

            yfmt = FormatStrFormatter('%.2f')
            ax.yaxis.set_major_formatter(yfmt)

            ax.set_xticks(ind + width / 2)
            ax.set_xticklabels(lbls)
            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(6)
                tick.label.set_rotation(90)
            self.save_graph(fig, out_put)
        else:
            print("ERROR: Histogram Poseview: " + out_put + "." + FORMAT_PNG)

    def generate_distance_graph(self, data, name_ligs, count_lig, out_put):
        if len(data) > 1:
            mask = np.tri(count_lig, k=-1)
            data = np.ma.array(data, mask=np.transpose(mask))
            data = np.flipud(data)
            _title = "Distances between Clusters (Angstrom)"
            _xlabel = "Clusters"
            _ylabel = "Clusters"
            fig, ax = plt.subplots()
            ax.set_title(_title)
            ax.set_xlabel(_xlabel)
            ax.set_ylabel(_ylabel)

            c = ax.pcolor(data, edgecolors='k', cmap=matplotlib.cm.rainbow)
            c.update_scalarmappable()

            for p, clr, value in zip(c.get_paths(), c.get_facecolors(), c.get_array()):
                _x, _y = p.vertices[:-2, :].mean(0)
                if np.all(clr[:3] > 0.5):
                    clr = (0.0, 0.0, 0.0)
                else:
                    clr = (1.0, 1.0, 1.0)
                ax.text(_x, _y, "%.2f" % value, ha='center', va='center',  fontsize=7, color=clr)

            fig.colorbar(c)

            ax.set_yticks(np.arange(data.shape[0]) + 0.5, minor=False)
            ax.set_xticks(np.arange(data.shape[1]) + 0.5, minor=False)

            ax.set_xticklabels(name_ligs, minor=False)
            ax.set_yticklabels(list(reversed(name_ligs)), minor=False)

            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(7)
                tick.tick2On = False
            for t in ax.yaxis.get_major_ticks():
                t.label.set_fontsize(7)
                t.tick2On = False
            self.save_graph(fig, out_put)

    def save_graph(self, fig, out_put):
        if FORMAT_SVG != None:
            fig.savefig(out_put+"."+ FORMAT_SVG, dpi=DPI, format=FORMAT_SVG )
        fig.savefig(out_put + "."+FORMAT_PNG , dpi=DPI, format=FORMAT_PNG)
        plt.cla()
        plt.clf()
        plt.close()


    @staticmethod
    def put_legend(ax, leyenda, clrs):
        for i in np.arange(len(leyenda)):
            ax.plot(1, 1.5, color=clrs[i], linewidth=2.5, linestyle="-", label=leyenda[i])
        ax.legend(loc='upper left', prop={'size': 6})

    @staticmethod
    def rotate_ticks_x(ang, ax):
        for tick in ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(8)
            tick.label.set_rotation(ang)


    @staticmethod
    def delete_column(datos, pos):
        for i in datos:
            i.pop(pos)

    def heat_map(self, legend, data, type_atom, y_title, out_put):
        fig, ax = plt.subplots()
        plt.imshow(data)
        plt.colorbar()
        plt.ylabel(y_title)

        plt.xticks(np.arange(len(legend)), legend)
        plt.yticks(np.arange(len(type_atom)), type_atom)

        for tick in ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(6)
            tick.label.set_rotation(45)
        self.save_graph(fig, out_put)
