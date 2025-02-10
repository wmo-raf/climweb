def test_page_meta_tags(self, page, meta_tags, check_image=True, check_description=True):
    # check title
    self.assertIsNotNone(meta_tags["title"])
    self.assertEqual(meta_tags["title"], page.get_meta_title())
    
    if check_description:
        # check meta_description
        self.assertIsNotNone(meta_tags["meta_description"])
        self.assertIsNotNone(meta_tags["meta_description"])
    
    # check meta url
    self.assertIsNotNone(meta_tags["meta_url"])
    self.assertEqual(meta_tags["meta_url"], page.full_url)
    
    if check_image:
        # check meta image
        self.assertIsNotNone(meta_tags["meta_image"])
        self.assertEqual(meta_tags["meta_image"], page.get_meta_image_url(self.dummy_request))
    
    # check site name
    self.assertIsNotNone(meta_tags["meta_name"])
    self.assertEqual(meta_tags["meta_name"], page.get_site().site_name)
