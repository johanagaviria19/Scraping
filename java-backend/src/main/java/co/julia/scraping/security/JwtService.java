package co.julia.scraping.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.security.MessageDigest;
import java.util.Date;

@Service
public class JwtService {
    private final Key key;
    public JwtService(@Value("${jwt.secret}") String secret) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(secret.getBytes(StandardCharsets.UTF_8));
            this.key = Keys.hmacShaKeyFor(bytes);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
    public String generate(String subject, long ttlMillis) {
        long now = System.currentTimeMillis();
        return Jwts.builder().setSubject(subject).setIssuedAt(new Date(now)).setExpiration(new Date(now + ttlMillis)).signWith(key, SignatureAlgorithm.HS256).compact();
    }
    public String validate(String token) {
        return Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token).getBody().getSubject();
    }
}