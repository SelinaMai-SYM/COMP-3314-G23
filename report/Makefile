.PHONY: all preview clean
all: Group_23.pdf
preview: sections_preview.pdf

sections_preview.pdf: sections_preview.tex preamble.tex sec3_experimental_evidence.tex sec4-7.tex references.bib neurips_2026.sty ../docs/figures/extension_pipeline_ppt_6_2.png
	pdflatex -interaction=nonstopmode -halt-on-error sections_preview.tex
	bibtex sections_preview
	pdflatex -interaction=nonstopmode -halt-on-error sections_preview.tex
	pdflatex -interaction=nonstopmode -halt-on-error sections_preview.tex

Group_23.pdf: main.tex preamble.tex frontmatter.tex sec3_experimental_evidence.tex sec4-7.tex references.bib neurips_2026.sty ../docs/figures/extension_pipeline_ppt_6_2.png
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cp main.pdf Group_23.pdf

clean:
	rm -f main.aux main.log main.out main.bbl main.blg main.fdb_latexmk main.fls main.pdf sections_preview.aux sections_preview.log sections_preview.out sections_preview.bbl sections_preview.blg sections_preview.fdb_latexmk sections_preview.fls
