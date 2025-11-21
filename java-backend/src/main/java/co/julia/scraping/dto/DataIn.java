package co.julia.scraping.dto;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public class DataIn {
    @NotNull
    private String keyword;
    @NotNull
    private Integer count;
    @NotNull
    private List<ProductIn> items;

    public String getKeyword() { return keyword; }
    public void setKeyword(String keyword) { this.keyword = keyword; }
    public Integer getCount() { return count; }
    public void setCount(Integer count) { this.count = count; }
    public List<ProductIn> getItems() { return items; }
    public void setItems(List<ProductIn> items) { this.items = items; }
}