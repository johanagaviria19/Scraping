package co.julia.scraping.service.spec;

import co.julia.scraping.domain.Product;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.time.Instant;

public class ProductSpecifications {
    public static Specification<Product> keywordContains(String keyword) {
        if (keyword == null || keyword.isBlank()) return null;
        String k = "%" + keyword.toLowerCase() + "%";
        return (root, q, cb) -> cb.or(
                cb.like(cb.lower(root.get("keyword")), k),
                cb.like(cb.lower(root.get("title")), k)
        );
    }

    public static Specification<Product> priceBetween(BigDecimal min, BigDecimal max) {
        if (min == null && max == null) return null;
        return (root, q, cb) -> {
            if (min != null && max != null) return cb.between(root.get("price"), min, max);
            if (min != null) return cb.greaterThanOrEqualTo(root.get("price"), min);
            return cb.lessThanOrEqualTo(root.get("price"), max);
        };
    }

    public static Specification<Product> ratingBetween(Double min, Double max) {
        if (min == null && max == null) return null;
        return (root, q, cb) -> {
            if (min != null && max != null) return cb.between(root.get("rating"), min, max);
            if (min != null) return cb.greaterThanOrEqualTo(root.get("rating"), min);
            return cb.lessThanOrEqualTo(root.get("rating"), max);
        };
    }

    public static Specification<Product> onlyDiscount(Boolean onlyDiscount) {
        if (onlyDiscount == null || !onlyDiscount) return null;
        return (root, q, cb) -> cb.isNotNull(root.get("discountPrice"));
    }

    public static Specification<Product> soldBetween(Integer min, Integer max) {
        if (min == null && max == null) return null;
        return (root, q, cb) -> {
            if (min != null && max != null) return cb.between(root.get("sold"), min, max);
            if (min != null) return cb.greaterThanOrEqualTo(root.get("sold"), min);
            return cb.lessThanOrEqualTo(root.get("sold"), max);
        };
    }

    public static Specification<Product> createdBetween(Instant from, Instant to) {
        if (from == null && to == null) return null;
        return (root, q, cb) -> {
            if (from != null && to != null) return cb.between(root.get("createdAt"), from, to);
            if (from != null) return cb.greaterThanOrEqualTo(root.get("createdAt"), from);
            return cb.lessThanOrEqualTo(root.get("createdAt"), to);
        };
    }

    public static Specification<Product> and(Specification<Product>... specs) {
        Specification<Product> result = null;
        for (Specification<Product> s : specs) {
            if (s == null) continue;
            result = (result == null) ? s : result.and(s);
        }
        return result;
    }
}