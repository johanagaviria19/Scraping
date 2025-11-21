package co.julia.scraping.repository;

import co.julia.scraping.domain.MongoProduct;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MongoProductRepository extends MongoRepository<MongoProduct, String> {
    Page<MongoProduct> findByKeywordContainingIgnoreCase(String keyword, Pageable pageable);
}