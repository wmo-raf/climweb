from wagtail import blocks
from wagtail.admin.forms import WagtailAdminModelForm

from pages.products.models import ProductPage


class ProductLayerForm(WagtailAdminModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")

        if instance:
            products_item_types = instance.product.product_item_types
            map_layers_field = self.fields.get("map_layers")

            for block_type, block in map_layers_field.block.child_blocks.items():
                block_name = "product_type"
                product_type_block = block.child_blocks.get(block_name)
                if product_type_block:
                    label = product_type_block.label or block_name
                    map_layers_field.block.child_blocks[block_type].child_blocks[block_name] = blocks.ChoiceBlock(
                        required=False, choices=products_item_types)
                    map_layers_field.block.child_blocks[block_type].child_blocks[block_name].name = block_name
                    map_layers_field.block.child_blocks[block_type].child_blocks[block_name].label = label

    class Meta:
        model = ProductPage
        fields = ["map_layers"]
