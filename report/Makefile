.PHONY: all clean
all: Group_23.pdf
main.pdf: main.tex references.bib neurips_2026.sty $(wildcard tables/*.tex) $(wildcard ../results/next_round/figures/*.pdf)
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
Group_23.pdf: main.pdf
	cp main.pdf Group_23.pdf
clean:
	rm -f main.aux main.log main.out main.bbl main.blg main.fdb_latexmk main.fls
