from django.test import TestCase
from rest_framework.test import APIClient
import ipdb


class TestAccountView(TestCase):
    def setUp(self):
        self.admin_data = {
            "username": "admin",
            "password": "1234",
            "is_superuser": True,
            "is_staff": True
        }

        self.admin_login_data = {
            "username": "admin",
            "password": "1234",
        }

    def test_create_account_and_login(self):
        client = APIClient()
        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        self.assertDictEqual(user, {
            'id': 1,
            'username': "admin",
            'is_superuser': True,
            'is_staff': True
        })

        # login
        response = client.post(
            '/api/login/', self.admin_login_data, format='json').json()

        self.assertIn('token', response.keys())


class TestInfrastructureView(TestCase):
    def setUp(self):
        self.admin_data = {
            "username": "admin",
            "password": "1234",
            "is_superuser": True,
            "is_staff": True
        }

        self.admin_login_data = {
            "username": "admin",
            "password": "1234",
        }

        self.level_data = {
            "name": "floor 1",
            "fill_priority": 2,
            "bike_spots": 1,
            "car_spots": 2
        }

        self.pricing_data = {
            "a_coefficient": 100,
            "b_coefficient": 100
        }

    def test_admin_create_level(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        level = client.post(
            '/api/levels/', self.level_data, format='json').json()

        self.assertEqual(level['id'], 1)
        self.assertEqual(level['available_spots']
                         ['available_bike_spots'], 1)
        self.assertEqual(level['available_spots']['available_car_spots'], 2)

    def test_get_level_info(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # create 2 levels
        level = client.post(
            '/api/levels/', self.level_data, format='json').json()

        level = client.post(
            '/api/levels/', self.level_data, format='json').json()

        levels = client.get('/api/levels/').json()

        self.assertEqual(len(levels), 2)

        for i, level in enumerate(levels):
            self.assertEqual(level['id'], i+1)
            self.assertEqual(level['available_spots']
                             ['available_bike_spots'], 1)
            self.assertEqual(level['available_spots']
                             ['available_car_spots'], 2)

    def test_admin_create_pricing(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        pricing = client.post(
            '/api/pricings/', self.pricing_data, format='json').json()

        pricing_data = self.pricing_data
        pricing_data['id'] = 1
        self.assertEqual(pricing, pricing_data)

    def test_only_admin_can_create_pricing(self):
        client = APIClient()

        response = client.post(
            '/api/pricings/', self.pricing_data, format='json')

        self.assertTrue(response.status_code, 401)


class TestVehicleView(TestCase):
    def setUp(self):
        self.admin_data = {
            "username": "admin",
            "password": "1234",
            "is_superuser": True,
            "is_staff": True
        }

        self.admin_login_data = {
            "username": "admin",
            "password": "1234",
        }

        self.level_data = {
            "name": "floor 1",
            "fill_priority": 2,
            "bike_spots": 0,
            "car_spots": 2
        }

        self.level_data_all = {
            "name": "floor 1",
            "fill_priority": 2,
            "bike_spots": 1,
            "car_spots": 2
        }

        self.pricing_data = {
            "a_coefficient": 100,
            "b_coefficient": 100
        }

        self.car_data = {
            "vehicle_type": "car",
            "license_plate": "AYO1029"
        }

        self.bike_data = {
            "vehicle_type": "bike",
            "license_plate": "CBR1010"
        }

    def test_create_vehicle_with_no_levels_gives_404(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # create pricing but no level
        client.post('/api/pricings/', self.pricing_data, format='json')

        response = client.post('api/vehicles/', self.car_data, format='json')

        self.assertTrue(response.status_code, 404)

    def test_create_vehicle_with_no_pricing_gives_404(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # create level but no pricing
        level = client.post(
            '/api/levels/', self.level_data, format='json').json()

        response = client.post('/api/vehicles/', self.car_data,
                               format='json')

        self.assertEqual(response.status_code, 404)

    def test_create_vehicle_takes_spot(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        level = client.post(
            '/api/levels/', self.level_data, format='json').json()

        pricing = client.post(
            '/api/pricings/', self.pricing_data, format='json')

        car = client.post('/api/vehicles/', self.car_data,
                          format='json').json()

        self.assertDictContainsSubset({
            "license_plate": "AYO1029",
            "vehicle_type": "car",
            "paid_at": None,
            "amount_paid": None,
            "spot": {
                "id": 1,
                "variety": "car",
                "level_name": "floor 1"
            }
        }, car)

        # only one parking spot left
        level = client.get('/api/levels/').json()[0]
        available_spots = level['available_spots']['available_car_spots']
        self.assertEqual(available_spots, 1)

    def test_cars_and_bikes_take_different_spots(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        level = client.post(
            '/api/levels/', self.level_data_all, format='json').json()

        pricing = client.post(
            '/api/pricings/', self.pricing_data, format='json')

        car = client.post('/api/vehicles/', self.car_data,
                          format='json').json()

        self.assertDictContainsSubset({
            "license_plate": "AYO1029",
            "vehicle_type": "car",
            "paid_at": None,
            "amount_paid": None,
        }, car)

        self.assertDictContainsSubset({
            "variety": "car",
            "level_name": "floor 1"
        }, car['spot'])

        # only one parking spot left
        level = client.get('/api/levels/').json()[0]
        available_car_spots = level['available_spots']['available_car_spots']

        self.assertEqual(available_car_spots, 1)
        available_bike_spots = level['available_spots']['available_bike_spots']

        self.assertEqual(available_bike_spots, 1)

        car = client.post('/api/vehicles/', self.car_data,
                          format='json').json()

        bike = client.post('/api/vehicles/', self.bike_data,
                           format='json').json()

        level = client.get('/api/levels/').json()[0]

        available_car_spots = level['available_spots']['available_car_spots']
        available_bike_spots = level['available_spots']['available_bike_spots']

        self.assertEqual(available_bike_spots, 0)
        self.assertEqual(available_car_spots, 0)

    def test_404_after_filling_all_spots(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        level = client.post(
            '/api/levels/', self.level_data_all, format='json').json()

        pricing = client.post(
            '/api/pricings/', self.pricing_data, format='json')

        car = client.post('/api/vehicles/', self.car_data,
                          format='json').json()

        self.assertDictContainsSubset({
            "license_plate": "AYO1029",
            "vehicle_type": "car",
            "paid_at": None,
            "amount_paid": None,
        }, car)

        self.assertDictContainsSubset({
            "variety": "car",
            "level_name": "floor 1"
        }, car['spot'])

        # only one parking spot left
        level = client.get('/api/levels/').json()[0]
        available_car_spots = level['available_spots']['available_car_spots']

        self.assertEqual(available_car_spots, 1)
        available_bike_spots = level['available_spots']['available_bike_spots']

        self.assertEqual(available_bike_spots, 1)

        car = client.post('/api/vehicles/', self.car_data,
                          format='json').json()

        bike = client.post('/api/vehicles/', self.bike_data,
                           format='json').json()

        level = client.get('/api/levels/').json()[0]

        available_car_spots = level['available_spots']['available_car_spots']
        available_bike_spots = level['available_spots']['available_bike_spots']

        self.assertEqual(available_bike_spots, 0)
        self.assertEqual(available_car_spots, 0)

        response = client.post('/api/vehicles/', self.car_data,
                               format='json')

        self.assertEqual(response.status_code, 404)

    def test_spots_are_filled_by_priority(self):
        # this time we establish to levels, to test if they are filled
        # in the correct order, even if there are some vehicles leaving

        level_1 = {
            "name": "floor 1",
            "fill_priority": 1,
            "bike_spots": 10,
            "car_spots": 10
        }

        level_2 = {
            "name": "floor 2",
            "fill_priority": 2,
            "bike_spots": 10,
            "car_spots": 10
        }

        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        level_1 = client.post(
            '/api/levels/', level_1, format='json').json()

        level_2 = client.post(
            '/api/levels/', level_2, format='json').json()

        pricing = client.post(
            '/api/pricings/', self.pricing_data, format='json')

        for _ in range(10):
            car = client.post('/api/vehicles/', self.car_data,
                              format='json')

        levels = client.get('/api/levels/').json()
        level_1 = levels[0]
        level_2 = levels[1]

        self.assertEqual(level_1['available_spots']['available_car_spots'], 0)
        self.assertEqual(level_2['available_spots']['available_car_spots'], 10)

        for _ in range(5):
            car = client.post('/api/vehicles/', self.car_data,
                              format='json')

        levels = client.get('/api/levels/').json()
        level_1 = levels[0]
        level_2 = levels[1]

        self.assertEqual(level_1['available_spots']['available_car_spots'], 0)
        self.assertEqual(level_2['available_spots']['available_car_spots'], 5)

        # now we remove a car from level 1

        client.put('/api/vehicles/1/')
        levels = client.get('/api/levels/').json()
        level_1 = levels[0]
        level_2 = levels[1]

        self.assertEqual(level_1['available_spots']['available_car_spots'], 1)
        self.assertEqual(level_2['available_spots']['available_car_spots'], 5)

        # add another car, and it should go to level 1
        car = client.post('/api/vehicles/', self.car_data,
                          format='json')

        levels = client.get('/api/levels/').json()
        level_1 = levels[0]
        level_2 = levels[1]

        self.assertEqual(level_1['available_spots']['available_car_spots'], 0)
        self.assertEqual(level_2['available_spots']['available_car_spots'], 5)

    def test_pricing_rules(self):
        client = APIClient()

        user = client.post(
            '/api/accounts/', self.admin_data, format='json').json()

        token = client.post(
            '/api/login/', self.admin_login_data, format='json').json()['token']

        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # create pricing but no level
        client.post('/api/pricings/', self.pricing_data, format='json')

        client.post(
            '/api/levels/', self.level_data, format='json')

        response = client.post('api/vehicles/', self.car_data, format='json')

        self.assertTrue(response.status_code, 404)
