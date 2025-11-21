package co.julia.scraping.service;

import co.julia.scraping.domain.Product;
import co.julia.scraping.dto.BenefitOut;
import co.julia.scraping.dto.HistogramBucket;
import co.julia.scraping.dto.ProductOut;
import co.julia.scraping.dto.StatsOut;
import co.julia.scraping.mapper.ProductMapper;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class StatsService {
    private final ProductQueryService queryService;
    public StatsService(ProductQueryService queryService) { this.queryService = queryService; }

    public StatsOut stats(String keyword, BigDecimal minPrice, BigDecimal maxPrice, Double minRating, Double maxRating, Boolean onlyDiscount, Integer minSold, Integer maxSold, java.time.Instant from, java.time.Instant to, int bins, int topN) {
        Page<Product> page = queryService.search(keyword, minPrice, maxPrice, minRating, maxRating, onlyDiscount, minSold, maxSold, from, to, Pageable.unpaged());
        List<Product> items = page.getContent();
        StatsOut out = new StatsOut();
        out.setTotal(items.size());
        long discountCount = items.stream().filter(p -> p.getDiscountPrice() != null).count();
        out.setDiscountCount(discountCount);
        BigDecimal min = items.stream().map(Product::getPrice).filter(p -> p != null).min(Comparator.naturalOrder()).orElse(null);
        BigDecimal max = items.stream().map(Product::getPrice).filter(p -> p != null).max(Comparator.naturalOrder()).orElse(null);
        out.setMinPrice(min);
        out.setMaxPrice(max);
        Double avgPrice = items.stream().map(Product::getPrice).filter(p -> p != null).mapToDouble(p -> p.doubleValue()).average().orElse(Double.NaN);
        out.setAvgPrice(Double.isNaN(avgPrice) ? null : avgPrice);
        Double avgRating = items.stream().map(Product::getRating).filter(r -> r != null).mapToDouble(r -> r).average().orElse(Double.NaN);
        out.setAvgRating(Double.isNaN(avgRating) ? null : avgRating);
        setPercentiles(out, items);
        out.setHistogram(buildHistogram(items, bins, min, max));
        out.setTopBenefit(buildTopBenefit(items, topN));
        out.setTopSold(buildTopSold(items, topN));
        return out;
    }

    private List<HistogramBucket> buildHistogram(List<Product> items, int bins, BigDecimal min, BigDecimal max) {
        List<HistogramBucket> buckets = new ArrayList<>();
        if (min == null || max == null) return buckets;
        if (bins <= 0) bins = 30;
        double mn = min.doubleValue();
        double mx = max.doubleValue();
        if (mx <= mn) {
            buckets.add(new HistogramBucket(min, max, items.stream().filter(p -> p.getPrice() != null).count()));
            return buckets;
        }
        double width = (mx - mn) / bins;
        long[] counts = new long[bins];
        for (Product p : items) {
            if (p.getPrice() == null) continue;
            double val = p.getPrice().doubleValue();
            int idx = (int) Math.floor((val - mn) / width);
            if (idx < 0) idx = 0;
            if (idx >= bins) idx = bins - 1;
            counts[idx]++;
        }
        for (int i = 0; i < bins; i++) {
            double start = mn + i * width;
            double end = (i == bins - 1) ? mx : (start + width);
            buckets.add(new HistogramBucket(BigDecimal.valueOf(start), BigDecimal.valueOf(end), counts[i]));
        }
        return buckets;
    }

    private List<BenefitOut> buildTopBenefit(List<Product> items, int topN) {
        List<BenefitOut> list = items.stream()
                .filter(p -> p.getPrice() != null && p.getPrice().doubleValue() > 0)
                .map(p -> {
                    double rating = (p.getRating() == null) ? 0.0 : p.getRating();
                    double benefit = rating / p.getPrice().doubleValue();
                    BenefitOut bo = new BenefitOut();
                    ProductOut po = ProductMapper.toOut(p);
                    bo.setProduct(po);
                    bo.setBenefit(benefit);
                    return bo;
                })
                .sorted(Comparator.comparing(BenefitOut::getBenefit).reversed())
                .limit(topN > 0 ? topN : 20)
                .collect(Collectors.toList());
        return list;
    }

    private void setPercentiles(StatsOut out, List<Product> items) {
        List<Double> prices = items.stream().map(Product::getPrice).filter(p -> p != null).map(BigDecimal::doubleValue).sorted().collect(Collectors.toList());
        if (prices.isEmpty()) return;
        out.setP25Price(BigDecimal.valueOf(percentile(prices, 0.25)));
        out.setP50Price(BigDecimal.valueOf(percentile(prices, 0.50)));
        out.setP75Price(BigDecimal.valueOf(percentile(prices, 0.75)));
        out.setP90Price(BigDecimal.valueOf(percentile(prices, 0.90)));
    }

    private double percentile(List<Double> sorted, double p) {
        int n = sorted.size();
        if (n == 0) return Double.NaN;
        double idx = p * (n - 1);
        int lo = (int) Math.floor(idx);
        int hi = (int) Math.ceil(idx);
        double w = idx - lo;
        double a = sorted.get(lo);
        double b = sorted.get(hi);
        return a + (b - a) * w;
    }

    private List<ProductOut> buildTopSold(List<Product> items, int topN) {
        return items.stream()
                .filter(p -> p.getSold() != null)
                .sorted(Comparator.comparing(Product::getSold).reversed())
                .limit(topN > 0 ? topN : 20)
                .map(ProductMapper::toOut)
                .collect(Collectors.toList());
    }
}