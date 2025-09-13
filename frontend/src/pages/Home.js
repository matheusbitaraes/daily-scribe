import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import SubscriptionForm from '../components/SubscriptionForm';
import Header from '../components/Header';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';



const Home = () => {

  return (
    <Box>
      <Header />
      <SubscriptionForm />
    </Box>
  );
};

export default Home;
