package co.julia.scraping.repository;

import co.julia.scraping.domain.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import java.util.Optional;

public interface ProductRepository extends JpaRepository<Product, Long>, JpaSpecificationExecutor<Product> {
    Optional<Product> findByUrl(String url);
    Page<Product> findByKeywordContainingIgnoreCase(String keyword, Pageable pageable);
}