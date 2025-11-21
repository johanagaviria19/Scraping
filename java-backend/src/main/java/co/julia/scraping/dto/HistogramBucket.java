package co.julia.scraping.dto;

import java.math.BigDecimal;

public class HistogramBucket {
    private BigDecimal start;
    private BigDecimal end;
    private long count;

    public HistogramBucket() {}
    public HistogramBucket(BigDecimal start, BigDecimal end, long count) {
        this.start = start; this.end = end; this.count = count;
    }
    public BigDecimal getStart() { return start; }
    public void setStart(BigDecimal start) { this.start = start; }
    public BigDecimal getEnd() { return end; }
    public void setEnd(BigDecimal end) { this.end = end; }
    public long getCount() { return count; }
    public void setCount(long count) { this.count = count; }
}