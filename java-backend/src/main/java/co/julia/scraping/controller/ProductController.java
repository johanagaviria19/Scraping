package co.julia.scraping.controller;

import co.julia.scraping.domain.Product;
import co.julia.scraping.dto.ProductOut;
import co.julia.scraping.mapper.ProductMapper;
import co.julia.scraping.repository.ProductRepository;
import co.julia.scraping.service.ProductQueryService;
import co.julia.scraping.repository.MongoProductRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.Instant;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductRepository repo;
    private final ProductQueryService queryService;
    private final MongoProductRepository mongoRepo;
    public ProductController(ProductRepository repo, ProductQueryService queryService, MongoProductRepository mongoRepo) { this.repo = repo; this.queryService = queryService; this.mongoRepo = mongoRepo; }

    @GetMapping
    public Page<ProductOut> list(@RequestParam(value = "keyword", required = false) String keyword,
                                 @RequestParam(value = "minPrice", required = false) BigDecimal minPrice,
                                 @RequestParam(value = "maxPrice", required = false) BigDecimal maxPrice,
                                 @RequestParam(value = "minRating", required = false) Double minRating,
                                 @RequestParam(value = "maxRating", required = false) Double maxRating,
                                 @RequestParam(value = "onlyDiscount", required = false) Boolean onlyDiscount,
                                 @RequestParam(value = "minSold", required = false) Integer minSold,
                                 @RequestParam(value = "maxSold", required = false) Integer maxSold,
                                 @RequestParam(value = "fromDate", required = false) String fromDate,
                                 @RequestParam(value = "toDate", required = false) String toDate,
                                 @PageableDefault(sort = {"createdAt"}, direction = Sort.Direction.DESC, size = 20) Pageable pageable) {
        Instant from = parseInstant(fromDate);
        Instant to = parseInstant(toDate);
        Page<Product> page = queryService.search(keyword, minPrice, maxPrice, minRating, maxRating, onlyDiscount, minSold, maxSold, from, to, pageable);
        return page.map(ProductMapper::toOut);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProductOut> get(@PathVariable Long id) {
        return repo.findById(id)
                .map(ProductMapper::toOut)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/mongo")
    public Page<ProductOut> listFromMongo(@RequestParam(value = "keyword", required = false) String keyword,
                                          @PageableDefault(sort = {"createdAt"}, direction = Sort.Direction.DESC, size = 20) Pageable pageable) {
        Page<co.julia.scraping.domain.MongoProduct> page;
        if (keyword == null || keyword.isBlank()) {
            page = mongoRepo.findAll(pageable);
        } else {
            page = mongoRepo.findByKeywordContainingIgnoreCase(keyword, pageable);
        }
        return page.map(ProductMapper::toOutMongo);
    }

    private Instant parseInstant(String s) {
        if (s == null || s.isBlank()) return null;
        try { return Instant.parse(s); } catch (Exception e) { return null; }
    }
}