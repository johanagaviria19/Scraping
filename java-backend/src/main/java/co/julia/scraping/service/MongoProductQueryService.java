package co.julia.scraping.service;

import co.julia.scraping.domain.Product;
import co.julia.scraping.mongo.ProductDocument;
import org.springframework.context.annotation.Profile;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Profile("mongo")
public class MongoProductQueryService implements ProductQueryService {
    private final MongoTemplate mongo;
    private final co.julia.scraping.mongo.MongoProductRepository repo;
    public MongoProductQueryService(MongoTemplate mongo, co.julia.scraping.mongo.MongoProductRepository repo) { this.mongo = mongo; this.repo = repo; }

    @Override
    public Page<Product> search(String keyword, BigDecimal minPrice, BigDecimal maxPrice, Double minRating, Double maxRating, Boolean onlyDiscount, Integer minSold, Integer maxSold, Instant from, Instant to, Pageable pageable) {
        Query q = new Query();
        Criteria c = new Criteria();
        boolean hasCriteria = false;
        if (keyword != null && !keyword.isBlank()) {
            Criteria k = new Criteria().orOperator(
                    Criteria.where("title").regex(keyword, "i"),
                    Criteria.where("keyword").regex(keyword, "i")
            );
            c = c.andOperator(k);
            hasCriteria = true;
        }
        if (minPrice != null || maxPrice != null) {
            Criteria pc = Criteria.where("price");
            if (minPrice != null) pc = pc.gte(minPrice);
            if (maxPrice != null) pc = pc.lte(maxPrice);
            c = hasCriteria ? c.andOperator(pc) : pc;
            hasCriteria = true;
        }
        if (minRating != null || maxRating != null) {
            Criteria rc = Criteria.where("rating");
            if (minRating != null) rc = rc.gte(minRating);
            if (maxRating != null) rc = rc.lte(maxRating);
            c = hasCriteria ? c.andOperator(rc) : rc;
            hasCriteria = true;
        }
        if (Boolean.TRUE.equals(onlyDiscount)) {
            Criteria dc = Criteria.where("discountPrice").ne(null);
            c = hasCriteria ? c.andOperator(dc) : dc;
            hasCriteria = true;
        }
        if (minSold != null || maxSold != null) {
            Criteria sc = Criteria.where("sold");
            if (minSold != null) sc = sc.gte(minSold);
            if (maxSold != null) sc = sc.lte(maxSold);
            c = hasCriteria ? c.andOperator(sc) : sc;
            hasCriteria = true;
        }
        if (from != null || to != null) {
            Criteria tc = Criteria.where("createdAt");
            if (from != null) tc = tc.gte(from);
            if (to != null) tc = tc.lte(to);
            c = hasCriteria ? c.andOperator(tc) : tc;
            hasCriteria = true;
        }
        if (hasCriteria) q.addCriteria(c);
        long total = mongo.count(q, ProductDocument.class);
        q.with(pageable);
        List<ProductDocument> docs = mongo.find(q, ProductDocument.class);
        List<Product> content = docs.stream().map(this::toDomain).collect(Collectors.toList());
        return new PageImpl<>(content, pageable, total);
    }

    private Product toDomain(ProductDocument d) {
        Product p = new Product();
        p.setId(null);
        p.setTitle(d.getTitle());
        p.setUrl(d.getUrl());
        p.setImage(d.getImage());
        p.setPrice(d.getPrice());
        p.setDiscountPrice(d.getDiscountPrice());
        p.setRating(d.getRating());
        p.setRatingCount(d.getRatingCount());
        p.setSold(d.getSold());
        p.setDescription(d.getDescription());
        p.setKeyword(d.getKeyword());
        p.setCreatedAt(d.getCreatedAt());
        return p;
    }

    @Override
    public java.util.Optional<Product> findByUrl(String url) {
        if (url == null || url.isBlank()) return java.util.Optional.empty();
        return repo.findByUrl(url).map(this::toDomain);
    }
}