from datetime import datetime
import io

from django.views.decorators.csrf import csrf_exempt


from django.db import connection, transaction, IntegrityError, ProgrammingError

from contextlib import closing

from django.utils.translation import gettext as _
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
import pandas as pd
import datatest as dt

from .serializers import RegistrationSerializer, ProductSerializer
from .models import Product

# pandas validate
dt.register_accessors()


# Create your views here.

def ValidateFileCSV(file):
    """
    Validar extension de archivo
    :param file:
    :return:
    """
    file = file.name.lower()
    if file.endswith(".csv"):
        return True
    else:
        return False


class RegistrationAPIView(generics.GenericAPIView):
    """ Registrar usuarios """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serializer_class = RegistrationSerializer

    def post(self, request):
        """
        Crear usuario
        :param request:
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "Error": False,
                "User": serializer.data,
                "Status": status.HTTP_201_CREATED,
                "Message": _("User created successfully")
            })

        return Response({
            "Error": True,
            "Status": status.HTTP_400_BAD_REQUEST,
            "Message": _("User not created")
        })


class ProductListAPIView(APIView):
    """ Clase para listar todos los productos """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """
        Obtener productos
        :param request:
        :return: Response
        """
        if request.method == 'GET':
            queryset = Product.objects.all()
            serializer_class = ProductSerializer(queryset, many=True)
            return Response({
                "Error": False,
                "Data": serializer_class.data,
                "Status": status.HTTP_200_OK,
                "Message": _("Products list")
            })

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """
        Crear productos
        :param request:
        """
        if request.method == 'POST':
            serializer_obj = ProductSerializer(data=request.data)
            if serializer_obj.is_valid(raise_exception=True):
                product_saved = serializer_obj.save()
                return Response({
                    "Error": False,
                    "Data": product_saved.name,
                    "Status": status.HTTP_201_CREATED,
                    "Message": _("Product created successfully")
                })

            return Response({
                "Error": True,
                "Status": status.HTTP_400_BAD_REQUEST,
                "Message": _(serializer_obj.errors)
            })


class ProductDetailAPIView(APIView):
    """ Clase producto """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.permission_classes = (permissions.IsAuthenticated,)

    # noinspection PyMethodMayBeStatic
    def get(self, request, pk):
        """
        Obtener los productos por id de base de datos
        :param request:
        :param pk:
        :return: Response
        """
        if request.method == 'GET':
            queryset = Product.objects.filter(id=pk)
            serializer_class = ProductSerializer(queryset, many=True)
            return Response({
                "Error": False,
                "Data": serializer_class.data,
                "Status": status.HTTP_200_OK,
                "Message": _("Products list")
            })

    # noinspection PyMethodMayBeStatic
    def put(self, request, pk):
        """
        Actualizar productos
        :param pk:
        :param request:
        """
        if request.method == 'PUT':
            product_obj = Product.objects.get(id=pk)
            serializer_obj = ProductSerializer(product_obj, data=request.data)
            if serializer_obj.is_valid(raise_exception=True):
                product_saved = serializer_obj.save()
                return Response({
                    "Error": False,
                    "Data": product_saved.name,
                    "Status": status.HTTP_200_OK,
                    "Message": _("Product updated successfully")
                })

            return Response({
                "Error": True,
                "Status": status.HTTP_400_BAD_REQUEST,
                "Message": _(serializer_obj.errors)
            })

    # noinspection PyMethodMayBeStatic
    def delete(self, request, pk):
        """
        Actualizar productos
        :param pk:
        :param request:
        """
        if request.method == 'DELETE':
            product_obj = Product.objects.filter(id=pk)
            if product_obj:
                product_delete = product_obj.delete()
                return Response({
                    "Error": False,
                    "Data": product_delete,
                    "Status": status.HTTP_200_OK,
                    "Message": _("Product deleted successfully")
                })

            return Response({
                "Error": False,
                "Status": status.HTTP_200_OK,
                "Message": _("Product not exists")
            })


class UploadClients(APIView):
    """
        Carga masiva de clientes
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.permission_classes = (permissions.IsAuthenticated,)
        self.headers = ["document", "first_name", "last_name", "email"]

        self.encoding = 'utf-8'
        self.list_data_success = []
        self.list_data_arch = []
        self.list_data_exists = []
        self.writer_file = io.StringIO()
        self.writer_file_invalid = io.StringIO()

    # noinspection PyMethodMayBeStatic
    def post(self, request, *args, **kwargs):
        """
        Funcion post para carga de archvio
        :param request:
        :param args:
        :param kwargs:
        """
        csv_file = request.FILES['file'] if 'file' in request.FILES else None
        if csv_file:
            # valida si el archivo es con la extesion csv
            if not ValidateFileCSV(csv_file):
                msg = _("The file you are trying to upload does not have the required CSV extension")
                return Response({
                    "Error": False,
                    "Status": status.HTTP_400_BAD_REQUEST,
                    "Message": msg
                })

        try:
            client_data = pd.read_csv(csv_file, encoding='utf-8', usecols=["document", "first_name", "last_name",
                                                                           "email"])
        except ValueError:
            msg = _("The file header is not as required.")
            return Response({
                "Error": True,
                "Status": status.HTTP_400_BAD_REQUEST,
                "Message": msg,
                "option": f"{_('The file header should be: ')}'document', 'first_name, 'last_name', 'email'"
            })

        except UnicodeDecodeError as err:
            msg = _("You are trying to load a file with an encoding other than UTF-8.")
            return Response({
                "Error": True,
                "Status": status.HTTP_400_BAD_REQUEST,
                "Message": msg
            })

        client_data = client_data.to_json()
        client_data = pd.read_json(client_data)
        for data in client_data.itertuples():
            with transaction.atomic():
                with closing(connection.cursor()) as cursor:
                    try:
                        cursor.execute("""INSERT INTO client (document, first_name, last_name, email ) VALUES 
                                        (%s,%s,%s,%s) ON CONFLICT (document) DO NOTHING RETURNING document""",
                                       (str(data.document), str(data.first_name), str(data.last_name),
                                        str(data.email)))
                    except IntegrityError as err:
                        print('Error')
                    try:
                        # row = cursor.fetchone()
                        for row in cursor:
                            self.list_data_success.append(str(row[0]))
                            print(row)
                        self.list_data_arch.append(str(data.document))
                    except ProgrammingError as err:
                        pass

        total_not_success = list(set(self.list_data_arch).difference(set(self.list_data_success)))
        total_created = len(self.list_data_success)
        total_not_created = len(total_not_success)
        if total_not_created:
            return Response({
                "Error": False,
                "Status": status.HTTP_200_OK,
                "Created": total_created,
                "Not created": total_not_created,
                "Client not exists": f"Clients already exist with document {total_not_success}",
                "Client exists": f"Clients created {self.list_data_success}",
            })

        return Response({
            "Error": False,
            "Status": status.HTTP_200_OK,
            "Created": total_created,
            "Not created": total_not_created,
            "Client": f"Clients created {self.list_data_success}"
        })


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@csrf_exempt
def create_file(request):
    """
        Crear archivo
    """

    file_name = f"client_file-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.csv"
    if request.method == 'POST':
        with transaction.atomic():
            """ Se uiliza el cursor importado de django """
            with closing(connection.cursor()) as cursor:
                try:
                    cursor.execute("""SELECT c.document, c.first_name, c.last_name, count(b.client_id_id)
                        as "Cantidad de facturas" FROM client as c  INNER JOIN bill b on c.id=b.client_id_id 
                        GROUP BY  c.document, c.first_name, c.last_name  """)
                except IntegrityError as err:
                    print('Error')
                try:
                    row = cursor.fetchone()
                    if row:
                        my_dict = {'Document': [row[0]], 'first_name': [row[1]], 'last_name': [row[2]],
                                   'number_of_invoices': [row[3]]}
                        dt_client = pd.DataFrame(my_dict)
                        print(dt_client)
                        dt_client.to_csv(file_name, index=False, encoding='UTF-8')

                        return Response({
                            "Error": False,
                            "Status": status.HTTP_200_OK,
                            "Clients": row,
                            "File": f"File saved with name {file_name}"
                        })
                    else:
                        return Response({
                            "Error": False,
                            "Status": status.HTTP_200_OK,
                            "Clients": [],
                        })
                except ProgrammingError as err:
                    return Response({
                        "Error": True,
                        "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    })


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def clients_manager(request):
    """
    Crear, actualizar, eliminar y listar
    :param request:
    """
    if request.method == 'GET':
        with closing(connection.cursor()) as cursor:
            try:
                """ Se uiliza el cursor importado de django """
                cursor.execute("""SELECT * FROM client """)
            except IntegrityError as err:
                print('Error')
            try:
                row = cursor.fetchall()
                print(row)
                return Response({
                    "Error": False,
                    "Status": status.HTTP_200_OK,
                    "Clients": row,
                })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'POST':
        client_data = JSONParser().parse(request)
        with closing(connection.cursor()) as cursor:
            try:
                """ Se uiliza el cursor importado de django """
                cursor.execute("""INSERT INTO client (document, first_name, last_name, email ) VALUES
                                                        (%s,%s,%s,%s) ON CONFLICT (document) DO NOTHING 
                                                        RETURNING document""", (str(client_data['document']),
                                                                                str(client_data['first_name']),
                                                                                str(client_data['last_name']),
                                                                                str(client_data['email'])))
            except IntegrityError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Clients created": row,
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": f"This client with document already exists {client_data['document']}",
                    })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
def clients_detail(request, pk):
    """
    Obtener por id
    :param request:
    :param pk:
    """
    if request.method == 'GET':
        with closing(connection.cursor()) as cursor:
            try:
                """ Se uiliza el cursor importado de django """
                cursor.execute("""SELECT * FROM client WHERE id=%s""", [pk])
            except IntegrityError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                return Response({
                    "Error": False,
                    "Status": status.HTTP_200_OK,
                    "Clients": row,
                })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'PUT':
        client_data = JSONParser().parse(request)
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""UPDATE client  SET first_name=%s, last_name=%s, email=%s WHERE id=%s 
                                RETURNING document""",
                               (str(client_data['first_name']),
                                str(client_data['last_name']),
                                str(client_data['email']), pk))
            except IntegrityError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                print(row)
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Clients": "Client updated",
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": f"This client not exists",
                    })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'DELETE':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""DELETE FROM client  WHERE id=%s RETURNING document""", [pk])
            except IntegrityError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                print(row)
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Clients": "Client deleted",
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": "This client not exists",
                    })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def bills_manager(request):
    """
    Crear, actualizar, eliminar y listar
    :param request:
    """
    if request.method == 'GET':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""SELECT * FROM bill """)
            except IntegrityError as err:
                print('Error')
            try:
                row = cursor.fetchall()
                print(row)
                return Response({
                    "Error": False,
                    "Status": status.HTTP_200_OK,
                    "Bills": row,
                })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'POST':
        bill_data = JSONParser().parse(request)
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute(
                    """INSERT INTO bill (client_id_id, company_name, nit, code ) VALUES  (%s,%s,%s,%s) RETURNING nit""",
                    (str(bill_data['client_id']),
                     str(bill_data['company_name']),
                     str(bill_data['nit']),
                     str(bill_data['code'])))
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Bills created": row,
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": f"This bill with company name already exists {bill_data['company_name']}",
                    })
            except ProgrammingError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
def bills_detail(request, pk):
    """
    Obtener por id
    :param request:
    :param pk:
    """
    if request.method == 'GET':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""SELECT * FROM bill WHERE id=%s""", [pk])
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                return Response({
                    "Error": False,
                    "Status": status.HTTP_200_OK,
                    "Clients": row,
                })
            except ProgrammingError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'PUT':
        bill_data = JSONParser().parse(request)
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""UPDATE bill  SET client_id_id=%s, company_name=%s, nit=%s, code=%s WHERE id=%s 
                                RETURNING id""",
                               (str(bill_data['client_id']),
                                str(bill_data['company_name']),
                                str(bill_data['nit']),
                                str(bill_data['code']), pk))
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                print(row)
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Clients": "Bill updated",
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": f"This Bill not exists",
                    })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'DELETE':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""DELETE FROM bill  WHERE id=%s RETURNING id""", [pk])
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                print(row)
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Clients": "Bill deleted",
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": "This Bill not exists",
                    })
            except ProgrammingError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def bills_product_manager(request):
    """
    Crear, actualizar, eliminar y listar
    :param request:
    """
    if request.method == 'GET':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""SELECT * FROM bill_product """)
            except IntegrityError as err:
                print('Error')
            try:
                row = cursor.fetchall()
                print(row)
                return Response({
                    "Error": False,
                    "Status": status.HTTP_200_OK,
                    "Bills": row,
                })
            except ProgrammingError as err:
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'POST':
        bill_product_data = JSONParser().parse(request)
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute(
                    """INSERT INTO bill_product (product_id_id, bill_id_id) VALUES  (%s,%s)  RETURNING id""",
                    (str(bill_product_data['product_id']), str(bill_product_data['bill_id'])))
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Bill product created": row,
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": f"This Bill product with id already exists {bill_product_data['client_id']}",
                    })
            except ProgrammingError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })


@permission_classes((IsAuthenticated,))
@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
def bills_product_detail(request, pk):
    """
    Obtener por id
    :param request:
    :param pk:
    """
    if request.method == 'GET':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""SELECT * FROM bill_product WHERE id=%s""", [pk])
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                return Response({
                    "Error": False,
                    "Status": status.HTTP_200_OK,
                    "Clients": row,
                })
            except ProgrammingError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })

    elif request.method == 'DELETE':
        """ Se uiliza el cursor importado de django """
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute("""DELETE FROM bill_product  WHERE id=%s RETURNING id""", [pk])
            except IntegrityError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
            try:
                row = cursor.fetchone()
                print(row)
                if row:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Clients": "Bill product deleted",
                    })
                else:
                    return Response({
                        "Error": False,
                        "Status": status.HTTP_200_OK,
                        "Message": "This Bill product not exists",
                    })
            except ProgrammingError as err:
                print(err)
                return Response({
                    "Error": True,
                    "Status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Data": "error"
                })
