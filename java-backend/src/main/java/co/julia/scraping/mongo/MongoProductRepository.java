package co.julia.scraping.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface MongoProductRepository extends MongoRepository<ProductDocument, String> {
    Optional<ProductDocument> findByUrl(String url);
}