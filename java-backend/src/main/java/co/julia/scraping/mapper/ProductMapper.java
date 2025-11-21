package co.julia.scraping.mapper;

import co.julia.scraping.domain.Product;
import co.julia.scraping.dto.ProductOut;

public class ProductMapper {
    public static ProductOut toOut(Product p) {
        ProductOut o = new ProductOut();
        o.setId(p.getId());
        o.setTitle(p.getTitle());
        o.setUrl(p.getUrl());
        o.setImage(p.getImage());
        o.setPrice(p.getPrice());
        o.setDiscountPrice(p.getDiscountPrice());
        o.setRating(p.getRating());
        o.setRatingCount(p.getRatingCount());
        o.setSold(p.getSold());
        o.setDescription(p.getDescription());
        o.setKeyword(p.getKeyword());
        o.setCreatedAt(p.getCreatedAt());
        return o;
    }
}