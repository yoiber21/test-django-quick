from django.db import models
from django.utils.translation import gettext as _


# Create your models here.
class Client(models.Model):
    """ Client model """
    id = models.AutoField(primary_key=True)
    document = models.CharField(max_length=12, blank=False, null=False, unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=False)
    last_name = models.CharField(max_length=150, blank=True, null=False)
    email = models.EmailField(max_length=100, blank=False, null=False)

    class Meta:
        db_table = 'client'
        ordering = ['id']

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)


class Bill(models.Model):
    """ Bill model """
    id = models.AutoField(primary_key=True)
    client_id = models.ForeignKey(Client, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150, blank=True, null=False)
    nit = models.CharField(max_length=150, blank=True, null=False)
    code = models.CharField(max_length=150, blank=True, null=False)

    class Meta:
        db_table = 'bill'
        ordering = ['id']

    def __str__(self):
        return "%s" % self.company_name


class Product(models.Model):
    """ Product model """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, blank=True, null=False)
    description = models.CharField(max_length=300, blank=True, null=False)
    date_created = models.DateTimeField(
        verbose_name=_("Creation date"), auto_now_add=True, null=False
    )
    expiration_date = models.DateField(verbose_name=_("Expiration Date"), null=True, default='DEFAULT VALUE')
    price = models.CharField(max_length=300, blank=True, null=False)

    class Meta:
        db_table = 'product'
        ordering = ['id']

    def __str__(self):
        return "%s" % self.name


class BillProduct(models.Model):
    """ Bill product model """
    id = models.AutoField(primary_key=True)
    bill_id = models.ForeignKey(Bill, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = 'bill_product'
        ordering = ['id']
