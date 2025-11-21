package co.julia.scraping.dto;

import java.math.BigDecimal;
import java.util.List;

public class StatsOut {
    private long total;
    private long discountCount;
    private BigDecimal minPrice;
    private BigDecimal maxPrice;
    private Double avgPrice;
    private Double avgRating;
    private BigDecimal p25Price;
    private BigDecimal p50Price;
    private BigDecimal p75Price;
    private BigDecimal p90Price;
    private List<HistogramBucket> histogram;
    private List<BenefitOut> topBenefit;
    private List<ProductOut> topSold;

    public long getTotal() { return total; }
    public void setTotal(long total) { this.total = total; }
    public long getDiscountCount() { return discountCount; }
    public void setDiscountCount(long discountCount) { this.discountCount = discountCount; }
    public BigDecimal getMinPrice() { return minPrice; }
    public void setMinPrice(BigDecimal minPrice) { this.minPrice = minPrice; }
    public BigDecimal getMaxPrice() { return maxPrice; }
    public void setMaxPrice(BigDecimal maxPrice) { this.maxPrice = maxPrice; }
    public Double getAvgPrice() { return avgPrice; }
    public void setAvgPrice(Double avgPrice) { this.avgPrice = avgPrice; }
    public Double getAvgRating() { return avgRating; }
    public void setAvgRating(Double avgRating) { this.avgRating = avgRating; }
    public BigDecimal getP25Price() { return p25Price; }
    public void setP25Price(BigDecimal p25Price) { this.p25Price = p25Price; }
    public BigDecimal getP50Price() { return p50Price; }
    public void setP50Price(BigDecimal p50Price) { this.p50Price = p50Price; }
    public BigDecimal getP75Price() { return p75Price; }
    public void setP75Price(BigDecimal p75Price) { this.p75Price = p75Price; }
    public BigDecimal getP90Price() { return p90Price; }
    public void setP90Price(BigDecimal p90Price) { this.p90Price = p90Price; }
    public List<HistogramBucket> getHistogram() { return histogram; }
    public void setHistogram(List<HistogramBucket> histogram) { this.histogram = histogram; }
    public List<BenefitOut> getTopBenefit() { return topBenefit; }
    public void setTopBenefit(List<BenefitOut> topBenefit) { this.topBenefit = topBenefit; }
    public List<ProductOut> getTopSold() { return topSold; }
    public void setTopSold(List<ProductOut> topSold) { this.topSold = topSold; }
}