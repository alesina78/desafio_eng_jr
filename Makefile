.PHONY: all bronze silver gold test app

bronze:
	python src/ingestion/download_uci_data.py

silver:
	python src/transformations/process_silver.py

gold:
	python src/gold/build_gold.py

test:
	pytest tests/ -v --tb=short

pipeline: test bronze silver gold
	@echo "✅ Pipeline completo executado com sucesso! Verifique data/silver/quality_reports/ e data/gold/"

app:
	streamlit run app.py