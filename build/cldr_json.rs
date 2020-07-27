mod cldr_json;

#[derive(Serialize, Deserialize)]
pub struct Data {
    #[serde(rename="_version")]
    version: u32,
    languages: Languages,
    scripts: Scripts,
    territories: Territories,
    variants: Variants,
    meta_zones: MetaZones,
    percent_formats: PercentFormats,
    decimal_formats: DecimalFormats,
    scientific_formats: ScientificFormats,
    eras: Eras,
    quarters: Quarters,
    months: Months,
    week_data: WeekData,
    days: Days,
    day_periods: DayPeriods,
    measurement_systems: MeasurementSystems,
    compound_unit_patterns: CompoundUnitPatterns,
    unit_patterns: UnitPatterns,
    unit_display_names: UnitDisplayNames,
    time_formats: TimeFormats,
    date_formats: DateFormats,
    time_zones: TimeZones,
    zone_formats: ZoneFormats,
    number_symbols: NumberSymbols,
    interval_formats: IntervalFormats,
    datetime_formats: DatetimeFormats,
    date_fields: DateFields,
    datetime_skeletons: DatetimeSkeletons,
    list_patterns: ListPatterns,
    currency_formats: CurrencyFormats,
    currency_names: CurrencyNames,
    currency_names_plural: CurrencyNamesPlural,
    currency_symbols: CurrencySymbols,
}

pub struct PercentFormats {

}

pub struct DecimalFormats {

}

pub struct Scripts {

}

pub struct ScientificFormats {

}

#[derive(Serialize, Deserialize)]
pub struct FormatStrings {
    short: String,
    medium: String,
    long: String,
    full: String
}

pub type TimeFormats = FormatStrings;
pub type DateFormats = FormatStrings;

pub struct NumberSymbols {
    #[serde(rename="minusSign")]
    minus_sign: String,
    #[serde(rename="percentSign")]
    percent_sign: String,
    list: String,
    infinity: String,
    #[serde(rename="perMille")]
    per_mille: String,
    decimal: String,
    nan: String,
    #[serde(rename="plusSign")]
    plus_sign: String,
    #[serde(rename="timeSeparator")]
    time_separator: String,
    alias: String,
    #[serde(rename="superscriptingExponent")]
    superscripting_exponent: String
}
