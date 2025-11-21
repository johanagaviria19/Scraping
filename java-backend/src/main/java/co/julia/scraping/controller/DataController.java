package co.julia.scraping.controller;

import co.julia.scraping.dto.DataIn;
import co.julia.scraping.service.DataService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class DataController {
    private final DataService dataService;
    public DataController(DataService dataService) { this.dataService = dataService; }

    @PostMapping("/data")
    public ResponseEntity<Map<String,Object>> ingest(@RequestBody DataIn in) {
        int saved = dataService.ingest(in);
        return ResponseEntity.ok(Map.of("received", in.getCount(), "saved", saved));
    }
}