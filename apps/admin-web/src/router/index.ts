import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import BagsView from '../views/BagsView.vue'
import LoginView from '../views/LoginView.vue'
import OrdersView from '../views/OrdersView.vue'
import PatternsView from '../views/PatternsView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    {
      path: '/',
      component: AdminLayout,
      redirect: '/bags',
      children: [
        { path: 'bags', component: BagsView },
        { path: 'patterns', component: PatternsView },
        { path: 'orders', component: OrdersView },
      ],
    },
  ],
})
