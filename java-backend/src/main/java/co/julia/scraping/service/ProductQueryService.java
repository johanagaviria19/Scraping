package co.julia.scraping.service;

import co.julia.scraping.domain.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.time.Instant;

public interface ProductQueryService {
    Page<Product> search(String keyword,
                         BigDecimal minPrice,
                         BigDecimal maxPrice,
                         Double minRating,
                         Double maxRating,
                         Boolean onlyDiscount,
                         Integer minSold,
                         Integer maxSold,
                         Instant from,
                         Instant to,
                         Pageable pageable);

    java.util.Optional<Product> findByUrl(String url);
}