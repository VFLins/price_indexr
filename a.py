from price_indexr.collect import (
    validate_integer_input,
    generate_filters,
    collect_search,
    strip_price_str,
)

prod = validate_integer_input(1)
q, kw = generate_filters(product=prod)
res = collect_search(q=q, product=prod, keywords=kw)
