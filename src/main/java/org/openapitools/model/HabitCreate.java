package org.openapitools.model;

import java.net.URI;
import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import org.openapitools.model.Frequency;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * HabitCreate
 */

@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-11-06T12:15:50.476882+05:00[Asia/Yekaterinburg]", comments = "Generator version: 7.27.0")
public class HabitCreate {

  private String name;

  private @Nullable String description;

  private Frequency frequency;

  public HabitCreate() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public HabitCreate(String name, Frequency frequency) {
    this.name = name;
    this.frequency = frequency;
  }

  public HabitCreate name(String name) {
    this.name = name;
    return this;
  }

  /**
   * Get name
   * @return name
   */
  @NotNull @Size(min = 1, max = 100) 
  @Schema(name = "name", example = "Зарядка", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("name")
  public String getName() {
    return name;
  }

  @JsonProperty("name")
  public void setName(String name) {
    this.name = name;
  }

  public HabitCreate description(@Nullable String description) {
    this.description = description;
    return this;
  }

  /**
   * Get description
   * @return description
   */
  @Size(max = 500) 
  @Schema(name = "description", example = "15 минут утром", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("description")
  public @Nullable String getDescription() {
    return description;
  }

  @JsonProperty("description")
  public void setDescription(@Nullable String description) {
    this.description = description;
  }

  public HabitCreate frequency(Frequency frequency) {
    this.frequency = frequency;
    return this;
  }

  /**
   * Get frequency
   * @return frequency
   */
  @NotNull @Valid 
  @Schema(name = "frequency", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("frequency")
  public Frequency getFrequency() {
    return frequency;
  }

  @JsonProperty("frequency")
  public void setFrequency(Frequency frequency) {
    this.frequency = frequency;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    HabitCreate habitCreate = (HabitCreate) o;
    return Objects.equals(this.name, habitCreate.name) &&
        Objects.equals(this.description, habitCreate.description) &&
        Objects.equals(this.frequency, habitCreate.frequency);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, description, frequency);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class HabitCreate {\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    frequency: ").append(toIndentedString(frequency)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(@Nullable Object o) {
    return o == null ? "null" : o.toString().replace("\n", "\n    ");
  }
}

