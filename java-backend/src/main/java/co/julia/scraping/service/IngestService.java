package co.julia.scraping.service;

import co.julia.scraping.dto.DataIn;

public interface IngestService {
    int ingest(DataIn in);
}