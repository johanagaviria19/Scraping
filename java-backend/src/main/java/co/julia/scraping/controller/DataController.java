package co.julia.scraping.controller;

import co.julia.scraping.dto.DataIn;
import co.julia.scraping.service.IngestService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api")
public class DataController {
    private final IngestService ingestService;
    public DataController(IngestService ingestService) { this.ingestService = ingestService; }

    @PostMapping("/data")
    public ResponseEntity<Map<String,Object>> ingest(@Valid @RequestBody DataIn in) {
        try {
            int saved = ingestService.ingest(in);
            return ResponseEntity.ok(Map.of("received", in.getCount(), "saved", saved));
        } catch (Exception e) {
            return ResponseEntity.status(503).body(Map.of("error", "storage_unavailable", "message", String.valueOf(e.getMessage())));
        }
    }
}