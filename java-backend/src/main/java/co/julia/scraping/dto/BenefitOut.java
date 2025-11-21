package co.julia.scraping.dto;

public class BenefitOut {
    private ProductOut product;
    private Double benefit;

    public ProductOut getProduct() { return product; }
    public void setProduct(ProductOut product) { this.product = product; }
    public Double getBenefit() { return benefit; }
    public void setBenefit(Double benefit) { this.benefit = benefit; }
}