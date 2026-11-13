.PHONY: all clean figures refresh-tables
PYTHON ?= python3
REPORT_DATE ?= 2026-11-13
all: Group_23.pdf
refresh-tables:
	cd .. && "$(PYTHON)" -m scripts.result_tables --report-output report/tables/edge_deletion_main.tex
	"$(PYTHON)" ../experiments/submission_refresh/reporting.py --root .. --date $(REPORT_DATE)
	cd .. && "$(PYTHON)" -m experiments.extension_verification.reporting --release-manifest configs/extension_verification/release_manifest.json
figures:
	bash ../scripts/build_ssc_pipeline.sh
figures/ssc_two_graph_pipeline.pdf: figures/ssc_two_graph_pipeline.tikz figures/ssc_two_graph_pipeline.tex ../scripts/build_ssc_pipeline.sh
	bash ../scripts/build_ssc_pipeline.sh
main.pdf: refresh-tables figures/ssc_two_graph_pipeline.pdf main.tex references.bib neurips_2026.sty $(wildcard tables/*.tex)
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
Group_23.pdf: main.pdf
	cp main.pdf Group_23.pdf
clean:
	rm -f main.aux main.log main.out main.bbl main.blg main.fdb_latexmk main.fls
