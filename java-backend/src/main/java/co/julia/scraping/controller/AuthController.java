package co.julia.scraping.controller;

import co.julia.scraping.domain.User;
import co.julia.scraping.repository.UserRepository;
import co.julia.scraping.security.JwtService;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final UserRepository users;
    private final PasswordEncoder encoder;
    private final JwtService jwt;
    public AuthController(UserRepository users, PasswordEncoder encoder, JwtService jwt) { this.users = users; this.encoder = encoder; this.jwt = jwt; }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String,String> body) {
        String username = body.get("username");
        String password = body.get("password");
        User u = new User();
        u.setUsername(username);
        u.setPassword(encoder.encode(password));
        u.setRoles(Set.of("USER"));
        users.save(u);
        return ResponseEntity.status(201).build();
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String,String> body) {
        String username = body.get("username");
        String password = body.get("password");
        User u = users.findByUsername(username).orElse(null);
        if (u == null || !encoder.matches(password, u.getPassword())) return ResponseEntity.status(401).build();
        String access = jwt.generate(username, 3600_000);
        String refresh = jwt.generate(username, 7_200_000);
        return ResponseEntity.ok(Map.of("accessToken", access, "refreshToken", refresh));
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(@RequestBody Map<String,String> body) {
        String token = body.get("refreshToken");
        String subject;
        try { subject = jwt.validate(token); } catch (Exception e) { return ResponseEntity.status(401).build(); }
        String access = jwt.generate(subject, 3600_000);
        return ResponseEntity.ok(Map.of("accessToken", access));
    }
}