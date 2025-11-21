package co.julia.scraping.service;

import co.julia.scraping.domain.Product;
import co.julia.scraping.dto.ProductIn;
import co.julia.scraping.repository.ProductRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
public class ProductService {
    private final ProductRepository repo;
    public ProductService(ProductRepository repo) { this.repo = repo; }

    @Transactional
    public Product upsert(ProductIn in, String keyword) {
        Product p = repo.findByUrl(in.getUrl()).orElseGet(Product::new);
        p.setUrl(in.getUrl());
        p.setTitle(in.getTitle());
        p.setImage(in.getImage());
        p.setPrice(in.getPrice());
        p.setDiscountPrice(in.getDiscountPrice());
        p.setRating(in.getRating());
        p.setRatingCount(in.getRatingCount());
        p.setSold(in.getSold());
        p.setDescription(in.getDescription());
        p.setKeyword(keyword);
        return repo.save(p);
    }
}