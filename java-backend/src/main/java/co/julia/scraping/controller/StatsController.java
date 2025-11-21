package co.julia.scraping.controller;

import co.julia.scraping.dto.StatsOut;
import co.julia.scraping.service.StatsService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.Instant;

@RestController
@RequestMapping("/api/products")
public class StatsController {
    private final StatsService statsService;
    public StatsController(StatsService statsService) { this.statsService = statsService; }

    @GetMapping("/stats")
    public ResponseEntity<StatsOut> stats(@RequestParam(value = "keyword", required = false) String keyword,
                                          @RequestParam(value = "minPrice", required = false) BigDecimal minPrice,
                                          @RequestParam(value = "maxPrice", required = false) BigDecimal maxPrice,
                                          @RequestParam(value = "minRating", required = false) Double minRating,
                                          @RequestParam(value = "maxRating", required = false) Double maxRating,
                                          @RequestParam(value = "onlyDiscount", required = false) Boolean onlyDiscount,
                                          @RequestParam(value = "minSold", required = false) Integer minSold,
                                          @RequestParam(value = "maxSold", required = false) Integer maxSold,
                                          @RequestParam(value = "fromDate", required = false) String fromDate,
                                          @RequestParam(value = "toDate", required = false) String toDate,
                                          @RequestParam(value = "bins", required = false, defaultValue = "30") int bins,
                                          @RequestParam(value = "topN", required = false, defaultValue = "20") int topN) {
        Instant from = parseInstant(fromDate);
        Instant to = parseInstant(toDate);
        StatsOut out = statsService.stats(keyword, minPrice, maxPrice, minRating, maxRating, onlyDiscount, minSold, maxSold, from, to, bins, topN);
        return ResponseEntity.ok(out);
    }

    private Instant parseInstant(String s) {
        if (s == null || s.isBlank()) return null;
        try { return Instant.parse(s); } catch (Exception e) { return null; }
    }
}