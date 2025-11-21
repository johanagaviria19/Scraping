package co.julia.scraping.service;

import co.julia.scraping.domain.Product;
import co.julia.scraping.repository.ProductRepository;
import co.julia.scraping.service.spec.ProductSpecifications;
import org.springframework.context.annotation.Profile;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;

@Service
@Profile("!mongo")
public class JpaProductQueryService implements ProductQueryService {
    private final ProductRepository repo;
    public JpaProductQueryService(ProductRepository repo) { this.repo = repo; }

    @Override
    public Page<Product> search(String keyword, BigDecimal minPrice, BigDecimal maxPrice, Double minRating, Double maxRating, Boolean onlyDiscount, Integer minSold, Integer maxSold, Instant from, Instant to, Pageable pageable) {
        Specification<Product> spec = ProductSpecifications.and(
                ProductSpecifications.keywordContains(keyword),
                ProductSpecifications.priceBetween(minPrice, maxPrice),
                ProductSpecifications.ratingBetween(minRating, maxRating),
                ProductSpecifications.onlyDiscount(onlyDiscount),
                ProductSpecifications.soldBetween(minSold, maxSold),
                ProductSpecifications.createdBetween(from, to)
        );
        if (spec == null) {
            return repo.findAll(pageable);
        }
        return repo.findAll(spec, pageable);
    }

    @Override
    public java.util.Optional<Product> findByUrl(String url) {
        if (url == null || url.isBlank()) return java.util.Optional.empty();
        return repo.findByUrl(url);
    }
}