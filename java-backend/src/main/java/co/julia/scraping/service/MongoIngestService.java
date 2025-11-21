package co.julia.scraping.service;

import co.julia.scraping.dto.DataIn;
import co.julia.scraping.dto.ProductIn;
import co.julia.scraping.mongo.MongoProductRepository;
import co.julia.scraping.mongo.ProductDocument;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
@Profile("mongo")
public class MongoIngestService implements IngestService {
    private final MongoProductRepository repo;
    public MongoIngestService(MongoProductRepository repo) { this.repo = repo; }

    @Override
    public int ingest(DataIn in) {
        if (in == null || in.getItems() == null) return 0;
        int saved = 0;
        for (ProductIn pi : in.getItems()) {
            if (pi == null || pi.getUrl() == null) continue;
            upsert(pi, in.getKeyword());
            saved++;
        }
        return saved;
    }

    private void upsert(ProductIn in, String keyword) {
        ProductDocument p = repo.findByUrl(in.getUrl()).orElse(null);
        if (p == null) {
            p = new ProductDocument();
            p.setCreatedAt(Instant.now());
            p.setUrl(in.getUrl());
        }
        p.setTitle(in.getTitle());
        p.setImage(in.getImage());
        p.setPrice(in.getPrice());
        p.setDiscountPrice(in.getDiscountPrice());
        p.setRating(in.getRating());
        p.setRatingCount(in.getRatingCount());
        p.setSold(in.getSold());
        p.setDescription(in.getDescription());
        p.setKeyword(keyword);
        repo.save(p);
    }
}