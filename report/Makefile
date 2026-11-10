.PHONY: all clean figures
all: Group_23.pdf
figures:
	bash ../scripts/build_ssc_pipeline.sh
figures/ssc_two_graph_pipeline.pdf: figures/ssc_two_graph_pipeline.tikz figures/ssc_two_graph_pipeline.tex ../scripts/build_ssc_pipeline.sh
	bash ../scripts/build_ssc_pipeline.sh
main.pdf: figures/ssc_two_graph_pipeline.pdf main.tex references.bib neurips_2026.sty $(wildcard tables/*.tex) $(wildcard ../results/next_round/figures/*.pdf)
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
Group_23.pdf: main.pdf
	cp main.pdf Group_23.pdf
clean:
	rm -f main.aux main.log main.out main.bbl main.blg main.fdb_latexmk main.fls
