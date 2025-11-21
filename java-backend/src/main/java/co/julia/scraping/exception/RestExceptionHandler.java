package co.julia.scraping.exception;

import com.mongodb.MongoException;
import jakarta.persistence.PersistenceException;
import org.springframework.dao.DataAccessException;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import jakarta.validation.ConstraintViolationException;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@ControllerAdvice
public class RestExceptionHandler {
    @ExceptionHandler({DataAccessException.class, PersistenceException.class, MongoException.class})
    public ResponseEntity<Map<String,Object>> storageUnavailable(Exception e) {
        return ResponseEntity.status(503).body(Map.of("error", "storage_unavailable", "message", String.valueOf(e.getMessage())));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String,Object>> invalid(MethodArgumentNotValidException e) {
        List<Map<String,Object>> fields = e.getBindingResult().getFieldErrors().stream()
                .map(fe -> Map.<String,Object>of("field", fe.getField(), "message", String.valueOf(fe.getDefaultMessage())))
                .collect(Collectors.toList());
        return ResponseEntity.badRequest().body(Map.<String,Object>of("error", "validation_error", "fieldErrors", fields));
    }

    @ExceptionHandler(BindException.class)
    public ResponseEntity<Map<String,Object>> bind(BindException e) {
        List<Map<String,Object>> fields = e.getBindingResult().getFieldErrors().stream()
                .map(fe -> Map.<String,Object>of("field", fe.getField(), "message", String.valueOf(fe.getDefaultMessage())))
                .collect(Collectors.toList());
        return ResponseEntity.badRequest().body(Map.<String,Object>of("error", "validation_error", "fieldErrors", fields));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<Map<String,Object>> constraint(ConstraintViolationException e) {
        List<Map<String,Object>> fields = e.getConstraintViolations().stream()
                .map(cv -> Map.<String,Object>of("field", String.valueOf(cv.getPropertyPath()), "message", String.valueOf(cv.getMessage())))
                .collect(Collectors.toList());
        return ResponseEntity.badRequest().body(Map.<String,Object>of("error", "validation_error", "fieldErrors", fields));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String,Object>> generic(Exception e) {
        return ResponseEntity.status(500).body(Map.of("error", "internal_error", "message", String.valueOf(e.getMessage())));
    }
}