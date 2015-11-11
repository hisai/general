-- MySQL dump 10.13  Distrib 5.6.23, for Linux (x86_64)
--
-- Host: localhost    Database: firmware
-- ------------------------------------------------------
-- Server version	5.6.23-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `chassis`
--

DROP TABLE IF EXISTS `chassis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `chassis` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `hostname` varchar(100) DEFAULT NULL,
  `serial_no` varchar(60) DEFAULT NULL,
  `product_name` varchar(100) DEFAULT NULL,
  `fw_version` varchar(60) DEFAULT NULL,
  `status` varchar(30) DEFAULT NULL,
  `site` varchar(10) DEFAULT NULL,
  `mysql_row_updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `mysql_row_created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  UNIQUE KEY `serial_no` (`serial_no`)
) ENGINE=InnoDB AUTO_INCREMENT=906 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hp`
--

DROP TABLE IF EXISTS `hp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `hp` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `serial_no` varchar(20) NOT NULL,
  `server_name` varchar(100) DEFAULT NULL,
  `ilo_version` varchar(60) DEFAULT NULL,
  `product_name` varchar(60) DEFAULT NULL,
  `system_rom_version` varchar(60) DEFAULT NULL,
  `position` varchar(10) DEFAULT NULL,
  `chassis` varchar(100) DEFAULT NULL,
  `mysql_row_updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `mysql_row_created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `serial_no` (`serial_no`),
  KEY `idx_server_name` (`server_name`(10)),
  KEY `idx_chassis` (`chassis`(10))
) ENGINE=InnoDB AUTO_INCREMENT=11697 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hp_incomplete`
--

DROP TABLE IF EXISTS `hp_incomplete`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `hp_incomplete` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `serial_no` varchar(20) NOT NULL,
  `server_name` varchar(100) DEFAULT NULL,
  `power_mgmt_ctrl_version` varchar(60) DEFAULT NULL,
  `ilo_version` varchar(60) DEFAULT NULL,
  `product_name` varchar(60) DEFAULT NULL,
  `system_rom_version` varchar(60) DEFAULT NULL,
  `position` varchar(10) DEFAULT NULL,
  `chassis` varchar(100) DEFAULT NULL,
  `mysql_row_created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `mysql_row_updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_server_name` (`server_name`(10)),
  KEY `idx_chassis` (`chassis`(10))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-11-02  5:09:13
