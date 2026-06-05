from services.text_excerpts import build_focused_excerpt


def test_focused_excerpt_centers_query_phrase():
    text = " ".join(
        [
            "intro",
            *[f"before{i}" for i in range(60)],
            "The wheel has 12 spokes and a center hub.",
            *[f"after{i}" for i in range(60)],
        ]
    )

    excerpt = build_focused_excerpt(text, "12 spokes", radius=80)

    assert excerpt.startswith("...\n")
    assert "12 spokes" in excerpt
    assert excerpt.endswith("\n...")


def test_focused_excerpt_matches_spoked_variant():
    text = "This line mentions a 12-spoked wheel in the answer explanation."

    excerpt = build_focused_excerpt(text, "12 spokes", radius=20)

    assert "12-spoked" in excerpt
