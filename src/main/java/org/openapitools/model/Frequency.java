package org.openapitools.model;

import java.net.URI;
import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonValue;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Gets or Sets Frequency
 */

@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-11-06T12:15:50.476882+05:00[Asia/Yekaterinburg]", comments = "Generator version: 7.27.0")
public enum Frequency {
  
  DAILY("DAILY"),
  
  WEEKLY("WEEKLY");

  private final String value;

  Frequency(String value) {
    this.value = value;
  }

  @JsonValue
  public String getValue() {
    return value;
  }

  @Override
  public String toString() {
    return String.valueOf(value);
  }

  @JsonCreator
  public static Frequency fromValue(String value) {
    for (Frequency b : Frequency.values()) {
      if (b.value.equals(value)) {
        return b;
      }
    }
    throw new IllegalArgumentException("Unexpected value '" + value + "'");
  }
}

