def test_page_meta_tags(test_case, page, meta_tags, request=None, check_image=True, check_description=True):
    # check title
    test_case.assertIsNotNone(meta_tags["title"])
    test_case.assertEqual(meta_tags["title"], page.get_meta_title())
    
    if check_description:
        # check meta_description
        test_case.assertIsNotNone(meta_tags["meta_description"])
        test_case.assertIsNotNone(meta_tags["meta_description"])
    
    # check meta url
    test_case.assertIsNotNone(meta_tags["meta_url"])
    test_case.assertEqual(meta_tags["meta_url"], page.full_url)
    
    if check_image:
        # check meta image
        test_case.assertIsNotNone(meta_tags["meta_image"])
        test_case.assertEqual(meta_tags["meta_image"], page.get_meta_image_url(request))
    
    # check site name
    test_case.assertIsNotNone(meta_tags["meta_name"])
    test_case.assertEqual(meta_tags["meta_name"], page.get_site().site_name)
