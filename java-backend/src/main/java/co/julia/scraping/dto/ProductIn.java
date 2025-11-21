package co.julia.scraping.dto;

import jakarta.validation.constraints.NotBlank;

import java.math.BigDecimal;

public class ProductIn {
    @NotBlank
    private String title;
    @NotBlank
    private String url;
    private String image;
    private BigDecimal price;
    private BigDecimal discountPrice;
    private Double rating;
    private Integer ratingCount;
    private Integer sold;
    private String description;

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }
    public String getImage() { return image; }
    public void setImage(String image) { this.image = image; }
    public BigDecimal getPrice() { return price; }
    public void setPrice(BigDecimal price) { this.price = price; }
    public BigDecimal getDiscountPrice() { return discountPrice; }
    public void setDiscountPrice(BigDecimal discountPrice) { this.discountPrice = discountPrice; }
    public Double getRating() { return rating; }
    public void setRating(Double rating) { this.rating = rating; }
    public Integer getRatingCount() { return ratingCount; }
    public void setRatingCount(Integer ratingCount) { this.ratingCount = ratingCount; }
    public Integer getSold() { return sold; }
    public void setSold(Integer sold) { this.sold = sold; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}